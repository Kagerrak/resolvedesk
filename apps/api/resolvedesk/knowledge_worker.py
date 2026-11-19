"""Durable leased parser/indexer. Fixture vectors are deterministic, not provider embeddings."""

import argparse
import hashlib
import math
import re
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import delete, or_, select
from sqlalchemy.exc import SQLAlchemyError

from .database import SessionLocal
from .models import DocumentVersion, KnowledgeChunk, KnowledgeDocument, KnowledgeJob, Workspace
from .operation_history import record
from .pdf_source import extract_pages


def sections(content: str, markdown: bool):
    heading, paragraphs, output = "Document", [], []

    def flush():
        body = "\n".join(paragraphs).strip()
        if body:
            for start in range(0, len(body), 1600):
                output.append((heading, body[start : start + 1600]))
        paragraphs.clear()

    for line in content.splitlines():
        if markdown and re.match(r"^#{1,6}\s+", line):
            flush()
            heading = re.sub(r"^#{1,6}\s+", "", line).strip() or "Untitled section"
        elif not line.strip():
            flush()
        else:
            paragraphs.append(line)
    flush()
    if not output:
        raise ValueError(
            "No readable body text found. Add paragraphs beneath the headings and upload a corrected file."
        )
    if len(output) > 500:
        raise ValueError(
            "Too many sections. Combine short paragraphs and upload a smaller document."
        )
    return output


def fixture_embedding(text: str):
    vector = [0.0] * 64
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        digest = hashlib.sha256(word.encode()).digest()
        vector[int.from_bytes(digest[:2], "big") % 64] += 1
    magnitude = math.sqrt(sum(x * x for x in vector))
    return [x / magnitude for x in vector] if magnitude else vector


def run_once() -> bool:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        candidate = db.execute(
            select(KnowledgeDocument.id, DocumentVersion.id, KnowledgeJob.id)
            .join(DocumentVersion, DocumentVersion.document_id == KnowledgeDocument.id)
            .join(KnowledgeJob, KnowledgeJob.version_id == DocumentVersion.id)
            .join(Workspace, Workspace.id == KnowledgeDocument.workspace_id)
            .where(
                KnowledgeDocument.archived.is_(False),
                Workspace.expires_at.is_(None) | (Workspace.expires_at > now),
                or_(
                    KnowledgeJob.status == "queued",
                    (KnowledgeJob.status == "processing") & (KnowledgeJob.lease_until < now),
                ),
            )
            .order_by(KnowledgeJob.created_at)
            .limit(1)
        ).first()
        if not candidate:
            return False
        # Same document → version → job lock order as Admin commands.
        doc = db.scalar(
            select(KnowledgeDocument)
            .where(KnowledgeDocument.id == candidate[0])
            .with_for_update(skip_locked=True)
        )
        if not doc or doc.archived:
            return False
        version = db.scalar(
            select(DocumentVersion).where(DocumentVersion.id == candidate[1]).with_for_update()
        )
        job = db.scalar(
            select(KnowledgeJob).where(KnowledgeJob.id == candidate[2]).with_for_update()
        )
        if not version or not job or job.status not in ("queued", "processing"):
            return False
        if job.status == "processing" and job.lease_until and job.lease_until >= now:
            return False
        if job.attempts >= 3:
            job.status = "failed"
            job.error = (
                "Indexing stopped after three interrupted attempts. Upload a corrected file."
            )
            version.status = "failed"
            job.lease_until = None
            job.lease_token = None
            record(db, doc.workspace_id, job.id, "indexing", "attempt_limit_reached", job.attempts)
            doc.revision += 1
            db.commit()
            return True
        job.attempts += 1
        job.status = "processing"
        job.lease_token = uuid4()
        job.lease_until = now + timedelta(minutes=2)
        job.error = None
        version.status = "processing"
        doc.revision += 1
        record(db, doc.workspace_id, job.id, "indexing", "started", job.attempts)
        token, job_id, version_id, doc_id, workspace_id = (
            job.lease_token,
            job.id,
            version.id,
            doc.id,
            doc.workspace_id,
        )
        source_bytes = version.source_bytes
        content, markdown = version.content, version.filename.lower().endswith(".md")
        db.commit()
    page_count = None
    try:
        if source_bytes is not None:
            pages = extract_pages(source_bytes)
            parsed = [
                ("PDF passage", body, number, fixture_embedding(body))
                for number, page in enumerate(pages, 1)
                for _, body in sections(page, False)
            ]
            page_count = len(pages)
        else:
            parsed = [
                (heading, body, None, fixture_embedding(heading + " " + body))
                for heading, body in sections(content, markdown)
            ]
            page_count = None
        if len(parsed) > 500:
            raise ValueError("Too many extracted sections. Split the document into smaller files.")
        error = None
    except ValueError as reason:
        parsed, error = [], str(reason)
    with SessionLocal() as db:
        doc = db.scalar(
            select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id).with_for_update()
        )
        version = db.scalar(
            select(DocumentVersion).where(DocumentVersion.id == version_id).with_for_update()
        )
        job = db.scalar(select(KnowledgeJob).where(KnowledgeJob.id == job_id).with_for_update())
        if (
            not doc
            or not version
            or not job
            or job.lease_token != token
            or job.status != "processing"
        ):
            return True  # Deleted or reclaimed lease: this worker must not publish stale results.
        db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.version_id == version_id))
        if not error and not doc.archived:
            for index, (heading, body, page_number, vector) in enumerate(parsed):
                db.add(
                    KnowledgeChunk(
                        workspace_id=workspace_id,
                        version_id=version_id,
                        ordinal=index + 1,
                        page_number=page_number,
                        heading=heading,
                        content=body,
                        embedding=vector,
                    )
                )
            version.page_count = page_count
            version.status = "ready"
            job.status = "succeeded"
        else:
            version.status = "failed"
            job.status = "failed"
            job.error = error or "Document archived during indexing."
        record(
            db,
            workspace_id,
            job.id,
            "indexing",
            "succeeded" if job.status == "succeeded" else "failed",
            job.attempts,
        )
        job.lease_until = None
        job.lease_token = None
        doc.revision += 1
        db.commit()
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.once:
        run_once()
    else:
        while True:
            try:
                if not run_once():
                    time.sleep(2)
            except SQLAlchemyError:
                # The lease remains durable after a database outage; no document content in logs.
                print("Knowledge worker unavailable; retrying shortly.", flush=True)
                time.sleep(2)
