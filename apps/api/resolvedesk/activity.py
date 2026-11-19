"""Scoped operational summaries and content-free recovery timelines."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import case, func, literal, select, union_all

from .inbox import membership
from .knowledge import DB, Command, Visitor, command, require_admin
from .models import (
    ApprovalRecord,
    DocumentVersion,
    GenerationRun,
    KnowledgeDocument,
    KnowledgeJob,
    OperationEvent,
    Ticket,
)

router = APIRouter()
Kind = Literal["all", "indexing", "generation", "handling"]
State = Literal[
    "all",
    "queued",
    "processing",
    "succeeded",
    "failed",
    "cancelled",
    "escalated",
    "confirmed",
    "archived",
    "deleted",
]


def operations(workspace_id: UUID, admin: bool):
    generation = (
        select(
            GenerationRun.id.label("id"),
            literal("generation").label("kind"),
            Ticket.subject.label("title"),
            GenerationRun.ticket_id.label("resource_id"),
            case(
                (GenerationRun.status == "running", "processing"), else_=GenerationRun.status
            ).label("status"),
            GenerationRun.created_at.label("updated_at"),
            Ticket.revision.label("revision"),
            literal(1).label("attempts"),
            GenerationRun.lease_until.label("lease_until"),
            GenerationRun.mode.label("mode"),
            literal(False).label("retired"),
        )
        .join(
            Ticket,
            (Ticket.id == GenerationRun.ticket_id)
            & (Ticket.workspace_id == GenerationRun.workspace_id),
        )
        .where(GenerationRun.workspace_id == workspace_id)
    )
    handling = (
        select(
            ApprovalRecord.id.label("id"),
            literal("handling").label("kind"),
            Ticket.subject.label("title"),
            ApprovalRecord.ticket_id.label("resource_id"),
            literal("confirmed").label("status"),
            ApprovalRecord.created_at.label("updated_at"),
            Ticket.revision.label("revision"),
            literal(1).label("attempts"),
            literal(None).cast(GenerationRun.lease_until.type).label("lease_until"),
            case(
                (ApprovalRecord.draft_id.is_(None), "ticket_changes"), else_="simulated_delivery"
            ).label("mode"),
            literal(False).label("retired"),
        )
        .join(
            Ticket,
            (Ticket.id == ApprovalRecord.ticket_id)
            & (Ticket.workspace_id == ApprovalRecord.workspace_id),
        )
        .where(ApprovalRecord.workspace_id == workspace_id)
    )
    queries = [generation, handling]
    if admin:
        latest = (
            select(func.max(OperationEvent.created_at))
            .where(
                OperationEvent.workspace_id == workspace_id,
                OperationEvent.operation_id.in_([KnowledgeJob.id, KnowledgeDocument.id]),
            )
            .correlate(KnowledgeJob, KnowledgeDocument)
            .scalar_subquery()
        )
        indexing = (
            select(
                KnowledgeJob.id.label("id"),
                literal("indexing").label("kind"),
                KnowledgeDocument.title.label("title"),
                KnowledgeDocument.id.label("resource_id"),
                case(
                    (KnowledgeDocument.deleted_at.is_not(None), "deleted"),
                    (KnowledgeDocument.archived.is_(True), "archived"),
                    else_=KnowledgeJob.status,
                ).label("status"),
                func.coalesce(latest, KnowledgeJob.created_at).label("updated_at"),
                KnowledgeDocument.revision.label("revision"),
                KnowledgeJob.attempts.label("attempts"),
                KnowledgeJob.lease_until.label("lease_until"),
                literal("fixture_indexing").label("mode"),
                KnowledgeDocument.archived.label("retired"),
            )
            .join(
                DocumentVersion,
                (DocumentVersion.id == KnowledgeJob.version_id)
                & (DocumentVersion.workspace_id == KnowledgeJob.workspace_id),
            )
            .join(
                KnowledgeDocument,
                (KnowledgeDocument.id == DocumentVersion.document_id)
                & (KnowledgeDocument.workspace_id == DocumentVersion.workspace_id),
            )
            .where(KnowledgeJob.workspace_id == workspace_id)
        )
        queries.append(indexing)
    return union_all(*queries).subquery()


def operation_view(row):
    expired = row.status == "processing" and row.lease_until and row.lease_until < datetime.now(UTC)
    can_retry = (
        row.kind == "indexing"
        and not row.retired
        and row.attempts < 3
        and (row.status == "failed" or bool(expired))
    )
    if row.kind == "indexing":
        if can_retry:
            next_action = (
                "Retry indexing. The previous attempt will be stopped before work resumes."
            )
        elif row.status in ("deleted", "archived"):
            next_action = (
                "Source unavailable for retrieval. Dependent drafts require evidence review."
            )
        elif row.status == "failed":
            next_action = "Attempt limit reached. Upload a corrected source."
        elif row.status == "processing":
            next_action = "Indexing is in progress. Refresh to check completion; recovery becomes available if it stops responding."
        elif row.status == "queued":
            next_action = "Waiting to index this source."
        else:
            next_action = "Open the source to inspect its sections and publication status."
    elif row.kind == "generation":
        next_action = "Open the ticket to review the saved draft or request a new one. Delivery still requires human approval."
    else:
        next_action = "Authorization recorded. Demo replies are simulated; no email was sent."
    return {
        **dict(row._mapping),
        "can_retry": bool(can_retry),
        "lease_expired": bool(expired),
        "next_action": next_action,
    }


@router.get("/workspaces/{workspace_id}/activity")
def list_activity(
    workspace_id: UUID,
    db: DB,
    visitor: Visitor,
    kind: Kind = "all",
    state: State = "all",
    offset: int = Query(0, ge=0, le=10000),
    limit: int = Query(25, ge=1, le=100),
):
    member = membership(db, workspace_id, visitor)
    rows = operations(workspace_id, member.role == "admin")
    query = select(rows)
    if kind != "all":
        query = query.where(rows.c.kind == kind)
    if state != "all":
        query = query.where(rows.c.status == state)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    result = db.execute(
        query.order_by(rows.c.updated_at.desc(), rows.c.kind, rows.c.id).offset(offset).limit(limit)
    )
    return {
        "items": [operation_view(row) for row in result],
        "total": total,
        "offset": offset,
        "limit": limit,
        "source_operations_admin_only": member.role != "admin",
        "gmail_recovery": "not_available",
    }


@router.get("/workspaces/{workspace_id}/activity/{kind}/{operation_id}")
def inspect_operation(
    workspace_id: UUID,
    kind: Literal["indexing", "generation", "handling"],
    operation_id: UUID,
    db: DB,
    visitor: Visitor,
):
    member = membership(db, workspace_id, visitor)
    rows = operations(workspace_id, member.role == "admin")
    row = db.execute(select(rows).where(rows.c.kind == kind, rows.c.id == operation_id)).first()
    if not row:
        raise HTTPException(404, "Operation not found.")
    timeline = []
    if kind == "indexing":
        events = db.scalars(
            select(OperationEvent)
            .where(
                OperationEvent.workspace_id == workspace_id,
                OperationEvent.operation_id.in_([operation_id, row.resource_id]),
            )
            .order_by(OperationEvent.created_at, OperationEvent.id)
        )
        timeline = [
            {
                "phase": event.phase,
                "attempt": event.attempt,
                "created_at": event.created_at,
                "actor": "You"
                if event.actor_id == visitor.user_id
                else "Knowledge worker"
                if not event.actor_id
                else "Workspace Admin",
            }
            for event in events
        ]
    elif kind == "handling":
        timeline = [
            {
                "phase": "confirmed_demo_reply"
                if row.mode == "simulated_delivery"
                else "confirmed_ticket_changes",
                "attempt": 1,
                "created_at": row.updated_at,
                "actor": "Workspace member",
            }
        ]
    else:
        timeline = [
            {
                "phase": "generation_requested",
                "attempt": 1,
                "created_at": row.updated_at,
                "actor": "Workspace member",
            }
        ]
    return {
        **operation_view(row),
        "timeline": timeline,
        "history_note": "Only recorded transitions are shown. Earlier operations may have no transition history. No source text, customer message bodies or credentials are included.",
    }


@router.post("/workspaces/{workspace_id}/activity/indexing/{operation_id}/retry")
def recover_indexing(
    workspace_id: UUID, operation_id: UUID, payload: Command, db: DB, visitor: Visitor
):
    require_admin(db, workspace_id, visitor)
    document_id = db.scalar(
        select(DocumentVersion.document_id)
        .join(
            KnowledgeJob,
            (KnowledgeJob.version_id == DocumentVersion.id)
            & (KnowledgeJob.workspace_id == DocumentVersion.workspace_id),
        )
        .where(KnowledgeJob.workspace_id == workspace_id, KnowledgeJob.id == operation_id)
    )
    if not document_id:
        raise HTTPException(404, "Operation not found.")
    return command(workspace_id, document_id, "retry", payload, db, visitor)
