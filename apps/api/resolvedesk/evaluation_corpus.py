"""Owned synthetic corpus preparation; no customer source content is replaced."""

import hashlib
import secrets
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select

from .database import SessionLocal
from .evaluation_dataset import load_dataset
from .identity import Identity
from .knowledge import Command, command, require_admin
from .knowledge_worker import run_once as index_once
from .models import (
    DocumentVersion,
    EvaluationRun,
    KnowledgeDocument,
    KnowledgeJob,
    Membership,
    Workspace,
)
from .operation_history import record


class EvaluationStopped(ValueError):
    pass


def guard(db, run_id, token):
    run = db.get(EvaluationRun, run_id)
    if not run:
        raise EvaluationStopped("Evaluation no longer exists.")
    require_admin(db, run.workspace_id, Identity(run.created_by, True))
    db.refresh(run, with_for_update=True)
    workspace = db.get(Workspace, run.workspace_id)
    if run.status not in ("preparing", "running") or run.lease_token != token:
        raise EvaluationStopped("Evaluation stopped or its processing lock changed.")
    if (
        not workspace
        or workspace.demo_owner != run.created_by
        or not workspace.expires_at
        or workspace.expires_at <= datetime.now(UTC)
    ):
        raise EvaluationStopped("Synthetic workspace expired or ownership changed.")
    dataset, digest = load_dataset(run.dataset_version)
    if digest != run.dataset_hash:
        raise EvaluationStopped(
            "Dataset content changed. Preserve this run and use a new dataset version."
        )
    return run, dataset


def seed_source(db, workspace_id, actor_id, title, content, filename):
    now = datetime.now(UTC)
    document_id, version_id, job_id = uuid4(), uuid4(), uuid4()
    digest = hashlib.sha256(content.encode()).hexdigest()
    db.add(
        KnowledgeDocument(
            id=document_id,
            workspace_id=workspace_id,
            title=title,
            created_by=actor_id,
            created_at=now,
        )
    )
    db.flush()
    db.add(
        DocumentVersion(
            id=version_id,
            workspace_id=workspace_id,
            document_id=document_id,
            filename=filename,
            content=content,
            content_hash=digest,
        )
    )
    db.flush()
    db.add(
        KnowledgeJob(id=job_id, workspace_id=workspace_id, version_id=version_id, created_at=now)
    )
    record(db, workspace_id, job_id, "indexing", "queued", actor_id=actor_id)
    return {"document_id": str(document_id), "version_id": str(version_id), "content_hash": digest}


def seed(run_id, token):
    with SessionLocal() as db:
        run, dataset = guard(db, run_id, token)
        if run.source_map:
            return
        previous = db.scalars(
            select(EvaluationRun)
            .where(
                EvaluationRun.workspace_id == run.workspace_id,
                EvaluationRun.dataset_hash == run.dataset_hash,
                EvaluationRun.id != run.id,
            )
            .order_by(EvaluationRun.created_at)
        ).all()
        reusable = {key: value for prior in previous for key, value in prior.source_map.items()}
        sources = {}
        for article in dataset.articles:
            existing = reusable.get(article.id) if article.publication != "conflict_only" else None
            if existing:
                doc = db.get(KnowledgeDocument, UUID(existing["document_id"]))
                version = db.get(DocumentVersion, UUID(existing["version_id"]))
                if (
                    not doc
                    or not version
                    or doc.workspace_id != run.workspace_id
                    or doc.deleted_at
                    or version.content_hash
                    != hashlib.sha256(article.content().encode()).hexdigest()
                ):
                    raise EvaluationStopped(
                        "A dataset source changed. Use a clean synthetic workspace."
                    )
                sources[article.id] = existing
            else:
                sources[article.id] = seed_source(
                    db,
                    run.workspace_id,
                    run.created_by,
                    article.title,
                    article.content(),
                    article.id + ".md",
                )
        workspace = db.get(Workspace, run.workspace_id)
        if not workspace:
            raise EvaluationStopped("Synthetic workspace disappeared.")
        probe_id = uuid4()
        marker = "PROBE_B_" + secrets.token_hex(12)
        db.add(
            Workspace(
                id=probe_id,
                name="Synthetic private evaluation probe",
                expires_at=workspace.expires_at,
            )
        )
        db.flush()
        db.add(Membership(workspace_id=probe_id, user_id=run.created_by, role="admin"))
        seed_source(
            db,
            probe_id,
            run.created_by,
            "Dedicated private export code for the Atlas workspace",
            "Dedicated private export code for the Atlas workspace. The Atlas private export code is "
            + marker
            + ". This source belongs only to the separate private probe workspace.",
            "private-probe.md",
        )
        run.source_map, run.probe_workspace_id, run.probe_marker = sources, probe_id, marker
        db.commit()


def source_ready(workspace_id, actor_id, source, publication):
    version_id = UUID(source["version_id"])
    with SessionLocal() as db:
        doc = db.get(KnowledgeDocument, UUID(source["document_id"]))
        version = db.get(DocumentVersion, version_id)
        if (
            not doc
            or not version
            or doc.workspace_id != workspace_id
            or version.workspace_id != workspace_id
            or doc.deleted_at
            or version.content_hash != source["content_hash"]
        ):
            raise EvaluationStopped("Evaluation source changed.")
        status = version.status
    if status in ("queued", "processing"):
        index_once(target_version_id=version_id)
    with SessionLocal() as db:
        doc = db.get(KnowledgeDocument, UUID(source["document_id"]))
        version = db.get(DocumentVersion, version_id)
        if not doc or not version:
            raise EvaluationStopped("Evaluation source disappeared.")
        if version.status in ("queued", "processing"):
            return False
        if version.status == "failed":
            raise EvaluationStopped(
                "Evaluation source indexing failed. Inspect Knowledge; no provider request was made."
            )
        if publication == "archived":
            if not doc.archived:
                command(
                    workspace_id,
                    doc.id,
                    "archive",
                    Command(expected_revision=doc.revision),
                    db,
                    Identity(actor_id, True),
                )
        elif publication == "published":
            if doc.archived:
                raise EvaluationStopped(
                    "A dataset source was archived. Do not restore it automatically."
                )
            if version.status != "published":
                command(
                    workspace_id,
                    doc.id,
                    "publish",
                    Command(expected_revision=doc.revision),
                    db,
                    Identity(actor_id, True),
                )
        elif doc.archived:
            raise EvaluationStopped(
                "The controlled source was archived before its cases completed."
            )
    return True


def prepare(run_id, token):
    seed(run_id, token)
    with SessionLocal() as db:
        run, dataset = guard(db, run_id, token)
        sources, workspace_id, actor_id, probe_id = (
            dict(run.source_map),
            run.workspace_id,
            run.created_by,
            run.probe_workspace_id,
        )
        db.commit()
    for article in dataset.articles:
        with SessionLocal() as db:
            guard(db, run_id, token)
        if not source_ready(workspace_id, actor_id, sources[article.id], article.publication):
            return False
    with SessionLocal() as db:
        guard(db, run_id, token)
        row = db.execute(
            select(KnowledgeDocument, DocumentVersion)
            .join(
                DocumentVersion,
                (DocumentVersion.document_id == KnowledgeDocument.id)
                & (DocumentVersion.workspace_id == KnowledgeDocument.workspace_id),
            )
            .where(KnowledgeDocument.workspace_id == probe_id)
        ).first()
        if not row:
            raise EvaluationStopped("Private probe source disappeared.")
        doc, version = row
        probe = {
            "document_id": str(doc.id),
            "version_id": str(version.id),
            "content_hash": version.content_hash,
        }
        db.commit()
    if not source_ready(probe_id, actor_id, probe, "published"):
        return False
    with SessionLocal() as db:
        run, _ = guard(db, run_id, token)
        run.prepared, run.status = True, "running"
        db.commit()
    return True


def set_conflict(db, run, active):
    source = run.source_map["conflicting-refunds"]
    doc = db.get(KnowledgeDocument, UUID(source["document_id"]))
    version = db.get(DocumentVersion, UUID(source["version_id"]))
    if not doc or not version or doc.deleted_at:
        raise EvaluationStopped("Controlled source unavailable.")
    if active and version.status != "published":
        command(
            run.workspace_id,
            doc.id,
            "publish",
            Command(expected_revision=doc.revision),
            db,
            Identity(run.created_by, True),
        )
    elif not active and version.status == "published" and not doc.archived:
        command(
            run.workspace_id,
            doc.id,
            "archive",
            Command(expected_revision=doc.revision),
            db,
            Identity(run.created_by, True),
        )


def closed_corpus(db, run, conflict_active):
    dataset, digest = load_dataset(run.dataset_version)
    if digest != run.dataset_hash:
        raise EvaluationStopped("Dataset version changed.")
    expected = {
        run.source_map[a.id]["version_id"]
        for a in dataset.articles
        if a.publication == "published" or (a.publication == "conflict_only" and conflict_active)
    }
    current = db.execute(
        select(DocumentVersion.id, DocumentVersion.content_hash)
        .join(
            KnowledgeDocument,
            (KnowledgeDocument.id == DocumentVersion.document_id)
            & (KnowledgeDocument.workspace_id == DocumentVersion.workspace_id),
        )
        .where(
            DocumentVersion.workspace_id == run.workspace_id,
            DocumentVersion.status == "published",
            KnowledgeDocument.archived.is_(False),
        )
    ).all()
    hashes = {s["version_id"]: s["content_hash"] for s in run.source_map.values()}
    if {str(row.id) for row in current} != expected or any(
        hashes[str(row.id)] != row.content_hash for row in current
    ):
        raise EvaluationStopped(
            "Published sources changed. Evaluation will not use unrelated or modified content."
        )


def cleanup_probe(db, run):
    if run.probe_workspace_id:
        probe = db.get(Workspace, run.probe_workspace_id)
        if probe:
            db.delete(probe)
        run.probe_workspace_id, run.probe_marker = None, None
