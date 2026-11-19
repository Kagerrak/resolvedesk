"""Evaluation authorization, durable requests and honest result denominators."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlparse
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select

from .config import settings
from .database import SessionLocal
from .evaluation_dataset import VERSION, load_dataset
from .evaluation_metrics import allocation
from .generation_provider import FIXTURE_MODEL, MODEL, PROMPT_VERSION
from .inbox import membership
from .knowledge import DB, Visitor, require_admin
from .models import (
    EvaluationCase,
    EvaluationReview,
    EvaluationRun,
    GenerationRun,
    KnowledgeDocument,
    Message,
    Ticket,
    Workspace,
)

router = APIRouter()
ACTIVE = ("queued", "preparing", "running")


class Evaluate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    dataset_version: str = Field(default=VERSION, max_length=80)
    split: Literal["tuning", "all"] = "all"
    method: Literal["exact-cosine-v1", "bm25-v1"] = "exact-cosine-v1"


class ReviewAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    output_hash: str = Field(min_length=64, max_length=64)
    reviewer_kind: Literal["agent_rubric", "member"]
    verdict: Literal["supported", "unsupported", "safe_escalation", "conservative_escalation"]
    note: str = Field(min_length=10, max_length=2000)


def output_hash(value: dict):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def local_live_gate():
    if any(
        urlparse(value).hostname not in ("localhost", "127.0.0.1", "::1")
        for value in [settings.database_url, settings.app_origin, settings.auth_url]
    ):
        raise ValueError("Live evaluation requires local application and database endpoints.")
    if not settings.live_ai_enabled or not settings.has_deepseek_key:
        raise ValueError(
            "Live evaluation remains disabled. Usage controls and local credentials are required."
        )


def queue_evaluation(db, workspace_id, visitor, payload: Evaluate, live=False):
    require_admin(db, workspace_id, visitor)
    workspace = db.get(Workspace, workspace_id)
    if not workspace or workspace.demo_owner != visitor.user_id or not workspace.expires_at:
        raise HTTPException(403, "Use an owned synthetic demo workspace for evaluation.")
    mode = "deepseek_sample" if live else "fixture"
    if live:
        local_live_gate()
        if payload.split != "all":
            raise HTTPException(422, "The bounded live sample requires the frozen full dataset.")
    try:
        dataset, digest = load_dataset(payload.dataset_version)
    except ValueError:
        raise HTTPException(422, "This evaluation dataset is not available.") from None
    existing = db.scalar(
        select(EvaluationRun).where(
            EvaluationRun.workspace_id == workspace_id,
            EvaluationRun.request_id == payload.request_id,
        )
    )
    if existing:
        if (
            existing.created_by,
            existing.dataset_hash,
            existing.method,
            existing.split,
            existing.mode,
        ) != (visitor.user_id, digest, payload.method, payload.split, mode):
            raise HTTPException(
                409, "This request identifier belongs to another evaluation intent."
            )
        return existing
    if db.scalar(
        select(EvaluationRun.id).where(
            EvaluationRun.workspace_id == workspace_id, EvaluationRun.status.in_(ACTIVE)
        )
    ):
        raise HTTPException(
            409, "An evaluation is already in progress. Inspect or cancel it first."
        )
    previous = db.scalars(
        select(EvaluationRun).where(EvaluationRun.workspace_id == workspace_id)
    ).all()
    if len(previous) >= 3:
        raise HTTPException(429, "This synthetic workspace has reached its three-evaluation limit.")
    owned_documents = {
        source["document_id"] for run in previous for source in run.source_map.values()
    }
    documents = db.scalars(
        select(KnowledgeDocument).where(KnowledgeDocument.workspace_id == workspace_id)
    ).all()
    if any(str(doc.id) not in owned_documents or doc.deleted_at for doc in documents):
        raise HTTPException(
            409,
            "Use a clean synthetic workspace. Evaluation never replaces your existing source content.",
        )
    if live:
        used = (
            db.scalar(
                select(func.count())
                .select_from(GenerationRun)
                .where(GenerationRun.workspace_id == workspace_id)
            )
            or 0
        )
        if used + len(dataset.live_sample) > 10:
            raise HTTPException(
                429, "The live sample must fit the existing ten-generation session limit."
            )
    run = EvaluationRun(
        workspace_id=workspace_id,
        request_id=payload.request_id,
        created_by=visitor.user_id,
        dataset_version=dataset.version,
        dataset_hash=digest,
        split=payload.split,
        method=payload.method,
        mode=mode,
        model=MODEL if live else FIXTURE_MODEL,
        prompt_version=PROMPT_VERSION if live else None,
        created_at=datetime.now(UTC),
        summary={
            "planned_cases": sum(
                payload.split == "all" or c.split == "tuning" for c in dataset.cases
            ),
            "completed_cases": 0,
            "live_case_ids": dataset.live_sample if live else [],
        },
    )
    db.add(run)
    db.flush()
    selected = [case for case in dataset.cases if payload.split == "all" or case.split == "tuning"]
    first = (
        db.scalar(select(func.max(Ticket.number)).where(Ticket.workspace_id == workspace_id))
        or 1000
    ) + 1
    tickets = [(case, uuid4()) for case in selected]
    for number, (case, ticket_id) in enumerate(tickets):
        db.add(
            Ticket(
                id=ticket_id,
                workspace_id=workspace_id,
                number=first + number,
                subject=case.subject,
                customer_name="Evaluation customer",
                customer_email="evaluation@example.com",
                created_at=datetime.now(UTC),
            )
        )
    db.flush()
    for case, ticket_id in tickets:
        db.add(
            Message(
                workspace_id=workspace_id,
                ticket_id=ticket_id,
                sender_name="Evaluation customer",
                sender_email="evaluation@example.com",
                body=case.body,
                created_at=datetime.now(UTC),
            )
        )
        db.add(
            EvaluationCase(
                workspace_id=workspace_id,
                run_id=run.id,
                ticket_id=ticket_id,
                case_key=case.id,
                definition=case.model_dump(),
            )
        )
    db.flush()
    return run


def scoped_run(db, workspace_id, run_id):
    run = db.scalar(
        select(EvaluationRun).where(
            EvaluationRun.workspace_id == workspace_id, EvaluationRun.id == run_id
        )
    )
    if not run:
        raise HTTPException(404, "Evaluation not found.")
    return run


def run_view(run):
    return {
        "id": run.id,
        "dataset_version": run.dataset_version,
        "dataset_hash": run.dataset_hash,
        "split": run.split,
        "method": run.method,
        "mode": run.mode,
        "model": run.model,
        "prompt_version": run.prompt_version,
        "status": run.status,
        "summary": run.summary,
        "source_versions": [
            {
                "article_id": key,
                "version_id": value["version_id"],
                "content_hash": value["content_hash"],
            }
            for key, value in run.source_map.items()
        ],
        "created_at": run.created_at,
        "finished_at": run.finished_at,
        "error": run.error,
        "limitations": "Authored synthetic labels; fixture retrieval. Agent rubric reviews are supplementary, not human ground truth. No numeric answer-quality release threshold is set.",
    }


@router.post("/workspaces/{workspace_id}/evaluations", status_code=202)
def start(workspace_id: UUID, payload: Evaluate, db: DB, visitor: Visitor):
    run = queue_evaluation(db, workspace_id, visitor, payload)
    result = run_view(run)
    db.commit()
    return result


@router.get("/workspaces/{workspace_id}/evaluations")
def list_runs(workspace_id: UUID, db: DB, visitor: Visitor):
    membership(db, workspace_id, visitor)
    return [
        {**run_view(run), "allocation": allocation(db, run)}
        for run in db.scalars(
            select(EvaluationRun)
            .where(EvaluationRun.workspace_id == workspace_id)
            .order_by(EvaluationRun.created_at.desc())
            .limit(20)
        )
    ]


@router.get("/workspaces/{workspace_id}/evaluations/{run_id}")
def inspect_run(workspace_id: UUID, run_id: UUID, db: DB, visitor: Visitor):
    membership(db, workspace_id, visitor)
    run = scoped_run(db, workspace_id, run_id)
    reviews = db.scalars(
        select(EvaluationReview)
        .where(EvaluationReview.workspace_id == workspace_id, EvaluationReview.run_id == run_id)
        .order_by(EvaluationReview.created_at.desc(), EvaluationReview.id.desc())
    ).all()
    latest = {}
    for review in reviews:
        latest.setdefault(str(review.case_id), review)
    counts = {
        verdict: sum(r.verdict == verdict for r in latest.values())
        for verdict in ("supported", "unsupported", "safe_escalation", "conservative_escalation")
    }
    return {
        **run_view(run),
        "allocation": allocation(db, run),
        "reviews": {
            "coverage": len(latest),
            "verdicts": counts,
            "origins": {
                kind: sum(r.reviewer_kind == kind for r in latest.values())
                for kind in ("agent_rubric", "member")
            },
            "support_denominator": counts["supported"] + counts["unsupported"],
        },
    }


@router.get("/workspaces/{workspace_id}/evaluations/{run_id}/cases")
def cases(
    workspace_id: UUID,
    run_id: UUID,
    db: DB,
    visitor: Visitor,
    split: Literal["all", "tuning", "held_out"] = "all",
    offset: int = Query(0, ge=0, le=60),
    limit: int = Query(20, ge=1, le=60),
):
    membership(db, workspace_id, visitor)
    scoped_run(db, workspace_id, run_id)
    query = select(EvaluationCase).where(
        EvaluationCase.workspace_id == workspace_id, EvaluationCase.run_id == run_id
    )
    if split != "all":
        query = query.where(EvaluationCase.definition["split"].as_string() == split)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(EvaluationCase.case_key).offset(offset).limit(limit))
    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "case_key": c.case_key,
                "split": c.definition["split"],
                "category": c.definition["category"],
                "subject": c.definition["subject"],
                "status": c.status,
                "metrics": c.metrics,
                "error": c.error,
                "has_provider_output": c.provider_output is not None,
                "source_hits": len(
                    set(c.definition["expected_sources"])
                    & set((c.retrieval or {}).get("ranked_articles", []))
                ),
                "source_expected": len(set(c.definition["expected_sources"])),
                "fixture_outcome": (c.fixture_output or {}).get("outcome"),
                "provider_outcome": (c.provider_output or {}).get("outcome"),
            }
            for c in rows
        ],
    }


def scoped_case(db, workspace_id, run_id, case_id):
    row = db.scalar(
        select(EvaluationCase).where(
            EvaluationCase.workspace_id == workspace_id,
            EvaluationCase.run_id == run_id,
            EvaluationCase.id == case_id,
        )
    )
    if not row:
        raise HTTPException(404, "Evaluation case not found.")
    return row


@router.get("/workspaces/{workspace_id}/evaluations/{run_id}/cases/{case_id}")
def inspect_case(workspace_id: UUID, run_id: UUID, case_id: UUID, db: DB, visitor: Visitor):
    membership(db, workspace_id, visitor)
    row = scoped_case(db, workspace_id, run_id, case_id)
    reviews = db.scalars(
        select(EvaluationReview)
        .where(
            EvaluationReview.workspace_id == workspace_id,
            EvaluationReview.run_id == run_id,
            EvaluationReview.case_id == case_id,
        )
        .order_by(EvaluationReview.created_at.desc(), EvaluationReview.id.desc())
    )
    return {
        "id": row.id,
        "definition": row.definition,
        "status": row.status,
        "retrieval": row.retrieval,
        "fixture_output": row.fixture_output,
        "provider_output": row.provider_output,
        "generation_id": row.generation_id,
        "metrics": row.metrics,
        "error": row.error,
        "reviews": [
            {
                "id": r.id,
                "output_hash": r.output_hash,
                "reviewer_kind": r.reviewer_kind,
                "verdict": r.verdict,
                "note": r.note,
                "created_at": r.created_at,
            }
            for r in reviews
        ],
    }


@router.post("/workspaces/{workspace_id}/evaluations/{run_id}/cases/{case_id}/reviews")
def review_output(
    workspace_id: UUID,
    run_id: UUID,
    case_id: UUID,
    payload: ReviewAssessment,
    db: DB,
    visitor: Visitor,
):
    require_admin(db, workspace_id, visitor)
    row = scoped_case(db, workspace_id, run_id, case_id)
    if not row.provider_output or row.provider_output.get("output_hash") != payload.output_hash:
        raise HTTPException(
            409, "Review the exact saved live output. Fixture output is not live model quality."
        )
    existing = db.scalar(
        select(EvaluationReview).where(
            EvaluationReview.workspace_id == workspace_id,
            EvaluationReview.request_id == payload.request_id,
        )
    )
    if existing:
        if (
            existing.case_id,
            existing.output_hash,
            existing.verdict,
            existing.note,
            existing.reviewer_kind,
            existing.reviewer_id,
        ) != (
            case_id,
            payload.output_hash,
            payload.verdict,
            payload.note,
            payload.reviewer_kind,
            visitor.user_id,
        ):
            raise HTTPException(409, "This review identifier belongs to another assessment.")
        return {"id": existing.id}
    review = EvaluationReview(
        workspace_id=workspace_id,
        run_id=run_id,
        case_id=case_id,
        request_id=payload.request_id,
        output_hash=payload.output_hash,
        reviewer_id=visitor.user_id,
        reviewer_kind=payload.reviewer_kind,
        verdict=payload.verdict,
        note=payload.note,
        created_at=datetime.now(UTC),
    )
    db.add(review)
    db.flush()
    result = {"id": review.id}
    db.commit()
    return result


@router.post("/workspaces/{workspace_id}/evaluations/{run_id}/cancel")
def cancel(workspace_id: UUID, run_id: UUID, db: DB, visitor: Visitor):
    require_admin(db, workspace_id, visitor)
    run = db.scalar(
        select(EvaluationRun)
        .where(EvaluationRun.workspace_id == workspace_id, EvaluationRun.id == run_id)
        .with_for_update()
    )
    if not run:
        raise HTTPException(404, "Evaluation not found.")
    if run.status in ACTIVE:
        run.status, run.finished_at = "cancelled", datetime.now(UTC)
        run.lease_token, run.lease_until = None, None
    pending = db.execute(
        select(EvaluationCase.ticket_id, GenerationRun.id)
        .join(
            GenerationRun,
            (GenerationRun.id == EvaluationCase.generation_id)
            & (GenerationRun.workspace_id == EvaluationCase.workspace_id)
            & (GenerationRun.ticket_id == EvaluationCase.ticket_id),
        )
        .where(
            EvaluationCase.workspace_id == workspace_id,
            EvaluationCase.run_id == run_id,
            GenerationRun.status.in_(("queued", "running")),
        )
    ).all()
    from .evaluation_corpus import cleanup_probe

    cleanup_probe(db, run)
    result = run_view(run)
    db.commit()
    # Parent intent commits before ticket locks; no lock-order cycle with a running case.
    for ticket_id, generation_id in pending:
        with SessionLocal() as cleanup:
            cleanup.scalar(
                select(Ticket)
                .where(Ticket.workspace_id == workspace_id, Ticket.id == ticket_id)
                .with_for_update()
            )
            generation = cleanup.scalar(
                select(GenerationRun)
                .where(
                    GenerationRun.workspace_id == workspace_id,
                    GenerationRun.ticket_id == ticket_id,
                    GenerationRun.id == generation_id,
                )
                .with_for_update()
            )
            if generation and generation.status in ("queued", "running"):
                generation.status = "cancelled"
                generation.error = "Evaluation cancelled. Saved drafts are retained; an in-flight request may still count toward allocation."
            cleanup.commit()
    return result


@router.get("/workspaces/{workspace_id}/evaluation-dataset")
def dataset_description(workspace_id: UUID, db: DB, visitor: Visitor):
    membership(db, workspace_id, visitor)
    dataset, digest = load_dataset()
    return {
        "version": dataset.version,
        "hash": digest,
        "article_count": len(dataset.articles),
        "case_count": len(dataset.cases),
        "tuning_count": sum(c.split == "tuning" for c in dataset.cases),
        "held_out_count": sum(c.split == "held_out" for c in dataset.cases),
        "live_sample_count": len(dataset.live_sample),
        "methods": ["exact-cosine-v1", "bm25-v1"],
        "label_origin": dataset.description,
        "split_policy": dataset.split_policy,
        "fixture_note": "Published extracts, not live AI quality. Public evaluation requests never enable paid calls.",
    }
