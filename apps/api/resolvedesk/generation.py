"""Human-requested durable drafting; generation cannot send or mutate ticket fields."""

import argparse
import hashlib
import json
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal
from .generation_provider import (
    FIXTURE_MODEL,
    MODEL,
    PROMPT_VERSION,
    deepseek_reply,
    fixture_reply,
    request_body,
    validate_reply,
)
from .handling import audit, editable_ticket
from .identity import Identity
from .inbox import membership, ticket_in_workspace
from .knowledge import DB, Visitor
from .models import (
    DraftRevision,
    EvaluationCase,
    EvaluationRun,
    GenerationRun,
    Membership,
    RetrievalRun,
    UsageMonth,
    Workspace,
)
from .retrieval import published_chunks, run_view

router = APIRouter()
PRICE_VERSION = "2026-11-18-deepseek-flash-peak-v1"
PRICE_EXPIRES = datetime(2026, 12, 18, tzinfo=UTC)
MONTH_CAP = 20_000_000
SESSION_CAP = 250_000
REQUEST_CAP = 100_000


class Generate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)
    retrieval_id: UUID
    request_id: UUID


def view(run):
    return {
        "id": run.id,
        "status": run.status,
        "mode": run.mode,
        "model": run.model,
        "retrieval_id": run.retrieval_id,
        "ticket_revision": run.ticket_revision,
        "citations": run.citations,
        "draft_id": run.draft_id,
        "error": run.error,
        "created_at": run.created_at,
        "prompt_version": run.prompt_version,
    }


def queue(db, workspace_id, ticket_id, payload, visitor, mode="fixture"):
    item = editable_ticket(db, workspace_id, ticket_id, visitor, payload.expected_revision)
    # Ticket locks protect revisions; a workspace lock also protects the shared
    # ten-generation limit when distinct tickets are submitted concurrently.
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"generation-quota:{workspace_id}"},
    )
    existing = db.scalar(
        select(GenerationRun).where(
            GenerationRun.workspace_id == workspace_id,
            GenerationRun.request_id == payload.request_id,
        )
    )
    if existing:
        if existing.ticket_id != ticket_id or existing.retrieval_id != payload.retrieval_id:
            raise HTTPException(409, "This request identifier belongs to a different generation.")
        return existing
    retrieval = db.scalar(
        select(RetrievalRun).where(
            RetrievalRun.workspace_id == workspace_id,
            RetrievalRun.ticket_id == ticket_id,
            RetrievalRun.id == payload.retrieval_id,
        )
    )
    if not retrieval or retrieval.ticket_revision != item.revision:
        raise HTTPException(409, "Find current supporting evidence before generating a draft.")
    count = db.scalar(
        select(func.count())
        .select_from(GenerationRun)
        .where(GenerationRun.workspace_id == workspace_id)
    )
    if count >= 10:
        raise HTTPException(
            429, "This demo has reached its generation limit. Your saved drafts remain available."
        )
    active = db.scalar(
        select(GenerationRun).where(
            GenerationRun.workspace_id == workspace_id,
            GenerationRun.ticket_id == ticket_id,
            GenerationRun.status.in_(["queued", "running"]),
        )
    )
    if active:
        raise HTTPException(409, "A draft is already being prepared. Inspect or cancel that run.")
    run = GenerationRun(
        workspace_id=workspace_id,
        ticket_id=ticket_id,
        retrieval_id=retrieval.id,
        request_id=payload.request_id,
        ticket_revision=item.revision,
        mode=mode,
        model=FIXTURE_MODEL if mode == "fixture" else MODEL,
        prompt_version=PROMPT_VERSION,
        created_by=visitor.user_id,
        created_at=datetime.now(UTC),
    )
    db.add(run)
    db.flush()
    return run


@router.post("/workspaces/{workspace_id}/tickets/{ticket_id}/generations", status_code=202)
def generate(workspace_id: UUID, ticket_id: UUID, payload: Generate, db: DB, visitor: Visitor):
    # Public API never accepts a provider mode/key or enables paid anonymous generation.
    run = queue(db, workspace_id, ticket_id, payload, visitor)
    result = view(run)
    db.commit()
    return result


def scoped_run(db, workspace_id, ticket_id, run_id):
    run = db.scalar(
        select(GenerationRun)
        .where(
            GenerationRun.workspace_id == workspace_id,
            GenerationRun.ticket_id == ticket_id,
            GenerationRun.id == run_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not run:
        raise HTTPException(404, "Generation not found.")
    return run


@router.get("/workspaces/{workspace_id}/tickets/{ticket_id}/generations/latest")
def latest(workspace_id: UUID, ticket_id: UUID, db: DB, visitor: Visitor):
    membership(db, workspace_id, visitor)
    ticket_in_workspace(db, workspace_id, ticket_id)
    run = db.scalar(
        select(GenerationRun)
        .where(GenerationRun.workspace_id == workspace_id, GenerationRun.ticket_id == ticket_id)
        .order_by(GenerationRun.created_at.desc())
        .limit(1)
    )
    return view(run) if run else None


@router.post("/workspaces/{workspace_id}/tickets/{ticket_id}/generations/{run_id}/cancel")
def cancel(workspace_id: UUID, ticket_id: UUID, run_id: UUID, db: DB, visitor: Visitor):
    item = ticket_in_workspace(db, workspace_id, ticket_id)
    editable_ticket(db, workspace_id, ticket_id, visitor, item.revision)
    run = scoped_run(db, workspace_id, ticket_id, run_id)
    if run.status in ("queued", "running"):
        run.status = "cancelled"
        run.error = "Draft generation cancelled. Your previous saved draft is unchanged."
    result = view(run)
    db.commit()
    return result


def context_for(db: Session, run: GenerationRun):
    visitor = Identity(run.created_by, run.mode == "fixture")
    item = editable_ticket(db, run.workspace_id, run.ticket_id, visitor, run.ticket_revision)
    if run.id is not None:
        evaluation = db.scalar(
            select(EvaluationRun)
            .join(
                EvaluationCase,
                (EvaluationCase.run_id == EvaluationRun.id)
                & (EvaluationCase.workspace_id == EvaluationRun.workspace_id),
            )
            .where(
                EvaluationCase.workspace_id == run.workspace_id,
                EvaluationCase.ticket_id == run.ticket_id,
                EvaluationCase.generation_id == run.id,
            )
        )
        if evaluation:
            member = db.get(Membership, (run.workspace_id, run.created_by))
            workspace = db.get(Workspace, run.workspace_id)
            if (
                not member
                or member.role != "admin"
                or not workspace
                or workspace.demo_owner != run.created_by
            ):
                raise ValueError("Evaluation Admin authorization changed.")
        if evaluation and (
            evaluation.status not in ("queued", "preparing", "running")
            or evaluation.mode != "deepseek_sample"
            or evaluation.created_by != run.created_by
        ):
            raise ValueError("This evaluation is no longer authorized for generation.")
    retrieval = db.scalar(
        select(RetrievalRun).where(
            RetrievalRun.workspace_id == run.workspace_id,
            RetrievalRun.ticket_id == run.ticket_id,
            RetrievalRun.id == run.retrieval_id,
        )
    )
    if not retrieval:
        raise ValueError("Evidence is no longer available. Retrieve again.")
    db.execute(published_chunks(run.workspace_id).with_for_update(read=True)).all()
    saved_evidence = run_view(db, retrieval)
    evidence = saved_evidence["results"]
    if saved_evidence["sources_changed"]:
        raise ValueError("Source material changed. Retrieve again before generating.")
    # Read-only application tool: model sees only this scoped, validated snapshot.
    return item, {
        "ticket": retrieval.query,
        "evidence": [
            {
                "citation_id": str(r["id"]),
                "title": r["title"],
                "version_id": str(r["version_id"]),
                "page_number": r["page_number"],
                "content": r["excerpt"],
            }
            for r in evidence
        ],
    }


def reserve(db, run, context):
    now = datetime.now(UTC)
    if now >= PRICE_EXPIRES:
        raise ValueError("AI pricing needs review. Paid drafting remains paused.")
    encoded = json.dumps(request_body(context), ensure_ascii=False).encode()
    if len(encoded) > 20000:
        raise ValueError("This conversation and evidence exceed the generation size limit.")
    # UTF-8 bytes plus schema/framing allowance conservatively upper-bound input tokens.
    # Conservative $1/M input and $2/M output exceed verified DeepSeek Flash peak rates.
    amount = (len(encoded) + 4096) + 2048 * 2
    if amount > REQUEST_CAP:
        raise ValueError("This request exceeds the per-request AI allowance.")
    month = now.strftime("%Y-%m")
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('resolvedesk-ai-budget',0))"))
    ledger = db.get(UsageMonth, month)
    if not ledger:
        ledger = UsageMonth(month=month, allocated_micros=0)
        db.add(ledger)
    session = db.scalar(
        select(func.coalesce(func.sum(GenerationRun.charge_micros), 0)).where(
            GenerationRun.workspace_id == run.workspace_id
        )
    )
    if (
        ledger.blocked
        or ledger.allocated_micros + amount > MONTH_CAP
        or session + amount > SESSION_CAP
    ):
        raise ValueError(
            "AI generation is paused for this allowance. Your saved drafts remain available."
        )
    ledger.allocated_micros += amount
    run.charge_micros = amount
    run.usage = {"month": month, "price_version": PRICE_VERSION, "reserved_micros": amount}


def reconcile(db, run, usage):
    if not usage or not run.charge_micros:
        return
    actual = usage["input_tokens"] + usage["output_tokens"] * 2
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('resolvedesk-ai-budget',0))"))
    ledger = db.get(UsageMonth, run.usage["month"])
    if not ledger:
        raise ValueError("AI allowance state unavailable. Reserved amount retained.")
    if actual > run.charge_micros:
        ledger.blocked = True
        run.status = "failed"
        run.error = "Provider usage exceeded reserved bounds. Paid drafting is paused for review."
        return
    ledger.allocated_micros -= run.charge_micros - actual
    run.charge_micros = actual
    run.usage = {**run.usage, **usage, "accounted_micros": actual}


def run_once(target_run_id: UUID | None = None):
    now = datetime.now(UTC)
    with SessionLocal() as db:
        # Expired running jobs are never automatically retried: provider acceptance may be unknown.
        expired = db.scalars(
            select(GenerationRun)
            .where(GenerationRun.status == "running", GenerationRun.lease_until < now)
            .with_for_update(skip_locked=True)
        ).all()
        for run in expired:
            run.status = "failed"
            run.error = "Generation was interrupted. Previous drafts are safe. Any uncertain AI allowance remains reserved."
        db.commit()
        allowed_modes = ["fixture"]
        if settings.live_ai_enabled and settings.has_deepseek_key:
            allowed_modes.append("deepseek")
        pending = select(GenerationRun.id).where(
            GenerationRun.status == "queued", GenerationRun.mode.in_(allowed_modes)
        )
        if target_run_id is not None:
            pending = pending.where(GenerationRun.id == target_run_id)
        candidate = db.scalar(pending.order_by(GenerationRun.created_at, GenerationRun.id).limit(1))
        if not candidate:
            return False
        # Match handling lock order: membership/workspace → ticket → run.
        candidate_run = db.get(GenerationRun, candidate)
        if not candidate_run:
            return False
        try:
            item, context = context_for(db, candidate_run)
            run = scoped_run(db, item.workspace_id, item.id, candidate)
            if run.status != "queued":
                return True
            if run.mode not in ("fixture", "deepseek"):
                raise ValueError("This provider is not enabled.")
            if run.mode == "deepseek":
                if not settings.live_ai_enabled or not settings.has_deepseek_key:
                    raise ValueError("Live AI remains disabled.")
                reserve(db, run, context)
            run.prompt_hash = hashlib.sha256(
                json.dumps(request_body(context), sort_keys=True).encode()
            ).hexdigest()
            run.status = "running"
            run.lease_until = now + timedelta(minutes=2)
            mode = run.mode
            db.commit()
        except (ValueError, HTTPException) as reason:
            db.rollback()
            run = db.get(GenerationRun, candidate)
            if run and run.status == "queued":
                run.status = "failed"
                run.error = (
                    str(reason.detail) if isinstance(reason, HTTPException) else str(reason)
                ) + " Your previous saved draft is safe."
                db.commit()
            return True
    usage = None
    try:
        if mode == "fixture":
            reply = fixture_reply(context)
        else:
            if not settings.deepseek_api_key or not settings.has_deepseek_key:
                raise ValueError("Provider credentials unavailable.")
            reply, usage = deepseek_reply(context, settings.deepseek_api_key.get_secret_value())
        reply = validate_reply(reply, context)
        error = None
    except (ValueError, httpx.HTTPError, KeyError, TypeError):
        reply = None
        error = "Draft generation could not produce a valid supported reply. Previous drafts are safe. Review evidence and try again."
    with SessionLocal() as db:
        run = db.get(GenerationRun, candidate)
        if not run:
            return True
        try:
            item, current = context_for(db, run)
            if current != context:
                raise ValueError("Evidence changed during generation.")
            # Consistent lock order: authorization → ticket → source → run → allowance.
            db.refresh(run, with_for_update=True)
            if usage:
                reconcile(db, run, usage)
            if run.status != "running":
                db.commit()
                return True
            if error or not reply:
                run.status, run.error = "failed", error
                db.commit()
                return True
            item.revision += 1
            draft = DraftRevision(
                workspace_id=item.workspace_id,
                ticket_id=item.id,
                ticket_revision=item.revision,
                body=reply.body,
                generation_id=run.id,
                citation_ids=reply.citation_ids,
                created_by=run.created_by,
                created_at=datetime.now(UTC),
            )
            db.add(draft)
            db.flush()
            run.draft_id, run.citations = draft.id, reply.citation_ids
            run.status = "escalated" if reply.outcome == "escalation" else "succeeded"
            run.error = reply.reason
            audit(
                db,
                item,
                Identity(run.created_by, mode == "fixture"),
                "draft_generated",
                {"generation_run": str(run.id), "draft_revision": str(draft.id), "mode": mode},
            )
            db.commit()
        except (ValueError, HTTPException):
            db.rollback()
            run = db.get(GenerationRun, candidate)
            if run and run.status == "running":
                run.status = "failed"
                run.error = "Ticket, access or evidence changed. Generated text was discarded; previous drafts are safe."
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
                print("Draft worker unavailable; saved drafts are safe.", flush=True)
                time.sleep(2)
