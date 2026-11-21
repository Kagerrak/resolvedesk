"""Durable synthetic evaluation; fixture work never dispatches a paid request."""

import argparse
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError

from .database import SessionLocal
from .evaluation import local_live_gate, output_hash, scoped_case
from .evaluation_corpus import (
    EvaluationStopped,
    cleanup_probe,
    closed_corpus,
    guard,
    prepare,
    set_conflict,
)
from .evaluation_metrics import summarize
from .generation import Generate, context_for, queue
from .generation import run_once as generate_once
from .generation_provider import FIXTURE_MODEL, fixture_reply, validate_reply
from .identity import Identity
from .knowledge import require_admin
from .knowledge_snapshot import lock_snapshot
from .models import (
    ApprovalRecord,
    DraftRevision,
    EvaluationCase,
    EvaluationRun,
    GenerationRun,
    Message,
    Ticket,
    Workspace,
)
from .retrieval import retrieve_ranked


def ticket_state(db, item):
    return {
        "status": item.status,
        "priority": item.priority,
        "assigned_to": item.assigned_to,
        "tags": item.tags,
        "agent_messages": db.scalar(
            select(func.count())
            .select_from(Message)
            .where(
                Message.workspace_id == item.workspace_id,
                Message.ticket_id == item.id,
                Message.kind != "customer",
            )
        )
        or 0,
    }


def frozen_input(db, item, definition):
    messages = db.scalars(
        select(Message)
        .where(Message.workspace_id == item.workspace_id, Message.ticket_id == item.id)
        .order_by(Message.created_at, Message.id)
    ).all()
    if (
        item.subject != definition["subject"]
        or len(messages) != 1
        or messages[0].body != definition["body"]
    ):
        raise EvaluationStopped(
            "An evaluation conversation changed. Preserve the run and review its inputs."
        )


def unapproved_effects(db, item, before, started):
    after = ticket_state(db, item)
    if after == before:
        return False
    approvals = db.scalars(
        select(ApprovalRecord)
        .where(
            ApprovalRecord.workspace_id == item.workspace_id,
            ApprovalRecord.ticket_id == item.id,
            ApprovalRecord.created_at >= started,
        )
        .order_by(ApprovalRecord.created_at, ApprovalRecord.id)
    ).all()
    if not approvals:
        return True
    approved_state = dict(before)
    for approval in approvals:
        for field, change in approval.content.get("actions", {}).items():
            if field not in ("status", "priority", "assigned_to", "tags") or not isinstance(
                change, dict
            ):
                return True
            if approved_state[field] != change.get("before") or "after" not in change:
                return True
            approved_state[field] = change["after"]
    unauthorized_messages = (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .where(
                Message.workspace_id == item.workspace_id,
                Message.ticket_id == item.id,
                Message.kind != "customer",
                ~select(ApprovalRecord.id)
                .where(
                    ApprovalRecord.workspace_id == item.workspace_id,
                    ApprovalRecord.message_id == Message.id,
                )
                .exists(),
            )
        )
        or 0
    )
    return bool(
        any(
            approved_state[field] != after[field]
            for field in ("status", "priority", "assigned_to", "tags")
        )
        or unauthorized_messages
    )


def release(run_id, token):
    with SessionLocal() as db:
        run = db.scalar(
            select(EvaluationRun)
            .where(EvaluationRun.id == run_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if run and run.lease_token == token:
            run.lease_token, run.lease_until = None, None
            db.commit()


def fail(run_id, token, message):
    with SessionLocal() as db:
        candidate = db.get(EvaluationRun, run_id)
        if not candidate:
            return
        lock_snapshot(db, candidate.workspace_id)
        run = db.scalar(
            select(EvaluationRun)
            .where(EvaluationRun.id == run_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if (
            not run
            or (token and run.lease_token != token)
            or run.status in ("completed", "cancelled", "failed")
        ):
            return
        run.status, run.error, run.finished_at = "failed", message, datetime.now(UTC)
        run.lease_token, run.lease_until = None, None
        for case in db.scalars(
            select(EvaluationCase).where(
                EvaluationCase.run_id == run_id,
                EvaluationCase.workspace_id == run.workspace_id,
                EvaluationCase.status == "running",
            )
        ):
            case.status, case.error, case.finished_at = "failed", message, datetime.now(UTC)
        run.summary = summarize(db, run)
        cleanup_probe(db, run)
        db.commit()


def claim(target_run_id, allow_live):
    if allow_live:
        if target_run_id is None:
            raise ValueError("Choose an exact local live evaluation.")
        local_live_gate()
    with SessionLocal() as db:
        query = select(EvaluationRun).where(
            EvaluationRun.status.in_(("queued", "preparing", "running")),
            or_(EvaluationRun.lease_until.is_(None), EvaluationRun.lease_until < datetime.now(UTC)),
        )
        if not allow_live:
            query = query.where(EvaluationRun.mode == "fixture")
        if target_run_id:
            query = query.where(EvaluationRun.id == target_run_id)
        candidate = db.scalar(query.order_by(EvaluationRun.created_at, EvaluationRun.id).limit(1))
        if not candidate:
            return None
        run_id = candidate.id
        try:
            require_admin(db, candidate.workspace_id, Identity(candidate.created_by, True))
            run = db.scalar(
                select(EvaluationRun)
                .where(EvaluationRun.id == run_id)
                .with_for_update(skip_locked=True)
                .execution_options(populate_existing=True)
            )
            if (
                not run
                or run.status not in ("queued", "preparing", "running")
                or (run.lease_until and run.lease_until > datetime.now(UTC))
            ):
                return None
            workspace = db.get(Workspace, run.workspace_id)
            if not workspace or workspace.demo_owner != run.created_by or not workspace.expires_at:
                raise EvaluationStopped("Use an active owned synthetic workspace.")
            token = uuid4()
            run.lease_token, run.lease_until = token, datetime.now(UTC) + timedelta(minutes=5)
            run.status = "running" if run.prepared else "preparing"
            prepared = run.prepared
            db.commit()
            return run_id, token, prepared
        except (HTTPException, EvaluationStopped):
            db.rollback()
    fail(run_id, None, "Evaluation access or synthetic workspace availability changed.")
    return None


def fixture_case(run_id, token, case_id):
    with SessionLocal() as db:
        run, _ = guard(db, run_id, token)
        case = scoped_case(db, run.workspace_id, run_id, case_id)
        if not case:
            raise EvaluationStopped("Evaluation case disappeared.")
        if case.fixture_output:
            return
        set_conflict(db, run, case.definition["conflict_source_active"])
        run, _ = guard(db, run_id, token)
        closed_corpus(db, run, case.definition["conflict_source_active"])
        item = db.get(Ticket, case.ticket_id)
        if not item:
            raise EvaluationStopped("Evaluation ticket disappeared.")
        frozen_input(db, item, case.definition)
        began = time.perf_counter()
        result = retrieve_ranked(
            run.workspace_id, item.id, db, Identity(run.created_by, True), run.method
        )
        retrieval_ms = (time.perf_counter() - began) * 1000
    with SessionLocal() as db:
        run, _ = guard(db, run_id, token)
        case = scoped_case(db, run.workspace_id, run_id, case_id)
        item = db.get(Ticket, case.ticket_id) if case else None
        if not case or not item:
            raise EvaluationStopped("Evaluation case disappeared.")
        closed_corpus(db, run, case.definition["conflict_source_active"])
        began = time.perf_counter()
        transient = GenerationRun(
            workspace_id=run.workspace_id,
            ticket_id=item.id,
            retrieval_id=UUID(str(result["id"])),
            ticket_revision=item.revision,
            created_by=run.created_by,
            mode="fixture",
        )
        item, context = context_for(db, transient)
        frozen_input(db, item, case.definition)
        before = ticket_state(db, item)
        response = validate_reply(fixture_reply(context), context)
        reverse = {value["version_id"]: key for key, value in run.source_map.items()}
        if any(str(row["version_id"]) not in reverse for row in result["results"]):
            raise EvaluationStopped("Retrieval included a source outside the fixed corpus.")
        case.retrieval = {
            "id": str(result["id"]),
            "method": run.method,
            "ranking": result["ranking"],
            "ranked_articles": [reverse[str(row["version_id"])] for row in result["results"]],
            "citation_ids": [str(row["id"]) for row in result["results"]],
            "source_versions": result["source_versions"],
            "source_hashes": {
                key: value["content_hash"]
                for key, value in run.source_map.items()
                if value["version_id"] in result["source_versions"]
            },
        }
        output = {
            **response.model_dump(),
            "model": FIXTURE_MODEL,
            "prompt_version": None,
            "mode": "fixture",
            "is_ai_quality": False,
        }
        output["output_hash"] = output_hash(output)
        case.fixture_output = output
        case.metrics = {
            **case.metrics,
            "retrieval_ms": round(retrieval_ms, 3),
            "fixture_ms": round((time.perf_counter() - began) * 1000, 3),
            "state_before": before,
            "workspace_disclosure": bool(run.probe_marker and run.probe_marker in response.body),
            "unapproved_action": unapproved_effects(db, item, before, case.started_at),
            "critical_checked": True,
        }
        run.summary = summarize(db, run)
        db.commit()


def provider_case(run_id, token, case_id):
    with SessionLocal() as db:
        run, _ = guard(db, run_id, token)
        case = scoped_case(db, run.workspace_id, run_id, case_id)
        if not case or not case.retrieval:
            raise EvaluationStopped("Retrieve and validate the case before live preparation.")
        if run.mode != "deepseek_sample" or case.case_key not in run.summary.get(
            "live_case_ids", []
        ):
            return True
        local_live_gate()
        if not case.generation_id:
            closed_corpus(db, run, case.definition["conflict_source_active"])
            item = db.get(Ticket, case.ticket_id)
            if not item:
                raise EvaluationStopped("Evaluation ticket disappeared.")
            frozen_input(db, item, case.definition)
            generation = queue(
                db,
                run.workspace_id,
                item.id,
                Generate(
                    expected_revision=item.revision,
                    retrieval_id=UUID(case.retrieval["id"]),
                    request_id=case.id,
                ),
                Identity(run.created_by, True),
                mode="deepseek",
            )
            if generation.mode != "deepseek" or generation.created_by != run.created_by:
                raise EvaluationStopped(
                    "Generation identifier conflicts with the live evaluation intent."
                )
            case.generation_id = generation.id
            db.commit()
        generation_id = case.generation_id
    with SessionLocal() as db:
        run, _ = guard(db, run_id, token)
        generation = db.get(GenerationRun, generation_id)
        if (
            not generation
            or generation.mode != "deepseek"
            or generation.created_by != run.created_by
        ):
            raise EvaluationStopped("Live generation is unavailable or changed.")
        needed = generation.status in ("queued", "running")
    began = time.perf_counter()
    progressed = generate_once(target_run_id=generation_id) if needed else False
    elapsed = round((time.perf_counter() - began) * 1000, 3) if progressed else None
    with SessionLocal() as db:
        run, _ = guard(db, run_id, token)
        case = scoped_case(db, run.workspace_id, run_id, case_id)
        generation = db.get(GenerationRun, generation_id)
        if not case or not generation:
            raise EvaluationStopped("Live evaluation case disappeared.")
        if generation.status in ("queued", "running"):
            return False
        if generation.status not in ("succeeded", "escalated") or not generation.draft_id:
            raise EvaluationStopped(
                "Live preparation failed or its outcome is unconfirmed. No paid retry was made; inspect the saved generation and allocation."
            )
        draft = db.get(DraftRevision, generation.draft_id)
        item = db.get(Ticket, case.ticket_id)
        if not draft or not item:
            raise EvaluationStopped("Saved live output disappeared.")
        closed_corpus(db, run, case.definition["conflict_source_active"])
        frozen_input(db, item, case.definition)
        output = {
            "body": draft.body,
            "citation_ids": draft.citation_ids,
            "outcome": "escalation" if generation.status == "escalated" else "answer",
            "reason": generation.error,
            "model": generation.model,
            "prompt_version": generation.prompt_version,
            "mode": "deepseek",
            "usage": generation.usage,
            "charge_micros": generation.charge_micros,
        }
        output["output_hash"] = output_hash(output)
        case.provider_output = output
        case.metrics = {
            **case.metrics,
            "workspace_disclosure": bool(
                case.metrics.get("workspace_disclosure")
                or (run.probe_marker and run.probe_marker in draft.body)
            ),
            "unapproved_action": bool(
                case.metrics.get("unapproved_action")
                or unapproved_effects(db, item, case.metrics["state_before"], case.started_at)
            ),
        }
        if elapsed is not None:
            case.metrics = {**case.metrics, "provider_ms": elapsed}
        db.commit()
    return True


def run_once(target_run_id: UUID | None = None, allow_live=False):
    claimed = claim(target_run_id, allow_live)
    if not claimed:
        return False
    run_id, token, prepared = claimed
    try:
        if not prepared and not prepare(run_id, token):
            release(run_id, token)
            return False
        with SessionLocal() as db:
            run, _ = guard(db, run_id, token)
            case = db.scalar(
                select(EvaluationCase)
                .where(
                    EvaluationCase.workspace_id == run.workspace_id,
                    EvaluationCase.run_id == run_id,
                    EvaluationCase.status.in_(("pending", "running")),
                )
                .order_by(EvaluationCase.case_key)
                .limit(1)
                .with_for_update()
            )
            if not case:
                run.status, run.finished_at = "completed", datetime.now(UTC)
                run.summary = summarize(db, run)
                run.lease_token, run.lease_until = None, None
                cleanup_probe(db, run)
                db.commit()
                return True
            if not case.fixture_output:
                if case.attempts >= 3:
                    raise EvaluationStopped(
                        "This case stopped after three interrupted preparation attempts."
                    )
                case.attempts += 1
            case.status, case.started_at = "running", case.started_at or datetime.now(UTC)
            case_id = case.id
            db.commit()
        fixture_case(run_id, token, case_id)
        if not provider_case(run_id, token, case_id):
            release(run_id, token)
            return False
        with SessionLocal() as db:
            run, _ = guard(db, run_id, token)
            case = scoped_case(db, run.workspace_id, run_id, case_id)
            if not case:
                raise EvaluationStopped("Evaluation case disappeared.")
            case.status, case.finished_at = "completed", datetime.now(UTC)
            run.summary = summarize(db, run)
            run.lease_token, run.lease_until = None, None
            db.commit()
        return True
    except EvaluationStopped as reason:
        fail(run_id, token, str(reason))
        return True
    except HTTPException as reason:
        fail(
            run_id,
            token,
            reason.detail
            if isinstance(reason.detail, str)
            else "Evaluation authorization or preparation changed.",
        )
        return True
    except ValueError:
        fail(
            run_id,
            token,
            "Evaluation validation failed. Saved results and allocation are retained; no paid retry was made.",
        )
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
                print("Evaluation worker unavailable; recorded work is retained.", flush=True)
                time.sleep(2)
