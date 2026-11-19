"""Human-initiated ticket handling; saving a draft never creates a message."""

from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .database import database
from .identity import Identity, identity
from .inbox import membership
from .models import (
    ApprovalRecord,
    AuditEvent,
    DraftRevision,
    Membership,
    Message,
    Ticket,
    Workspace,
)
from .ticket_views import DraftView, EventView, MessageView, TicketDetail, TicketView

router = APIRouter()
DB = Annotated[Session, Depends(database)]
Visitor = Annotated[Identity, Depends(identity)]


class HandlingChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)
    status: Literal["open", "pending", "resolved"]
    priority: Literal["low", "normal", "high", "urgent"]
    assigned_to: str | None = Field(max_length=128)
    reopen: bool = False
    tags: list[str] | None = Field(default=None, max_length=10)

    @field_validator("tags")
    @classmethod
    def normalized_tags(cls, tags):
        if tags is None:
            return None
        result = sorted({t.strip().lower() for t in tags if t.strip()})
        if any(len(t) > 32 or not all(c.isalnum() or c in " -_" for c in t) for t in result):
            raise ValueError(
                "Use tags of up to 32 letters, numbers, spaces, hyphens or underscores."
            )
        return result


class SaveDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)
    body: str = Field(max_length=20000)


def read_detail(db: Session, item: Ticket, visitor: Identity) -> TicketDetail:
    messages = db.scalars(
        select(Message)
        .where(Message.workspace_id == item.workspace_id, Message.ticket_id == item.id)
        .order_by(Message.created_at, Message.id)
    )
    draft = db.scalar(
        select(DraftRevision)
        .where(DraftRevision.workspace_id == item.workspace_id, DraftRevision.ticket_id == item.id)
        .order_by(DraftRevision.ticket_revision.desc())
        .limit(1)
    )
    events = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.workspace_id == item.workspace_id, AuditEvent.ticket_id == item.id)
        .order_by(AuditEvent.created_at, AuditEvent.id)
    )
    return TicketDetail(
        **TicketView.model_validate(item).model_dump(),
        messages=[MessageView.model_validate(m) for m in messages],
        draft=DraftView.model_validate(draft) if draft else None,
        events=[
            EventView(
                id=e.id,
                actor="You" if e.actor_id == visitor.user_id else "Workspace member",
                action=e.action,
                changes=e.changes,
                created_at=e.created_at,
            )
            for e in events
        ],
    )


def editable_ticket(
    db: Session,
    workspace_id: UUID,
    ticket_id: UUID,
    visitor: Identity,
    expected_revision: int | None,
) -> Ticket:
    # Hold authorization rows until commit; every handling command uses this lock order.
    member = db.scalar(
        select(Membership)
        .join(Workspace)
        .where(
            Membership.workspace_id == workspace_id,
            Membership.user_id == visitor.user_id,
            Workspace.expires_at.is_(None) | (Workspace.expires_at > datetime.now(UTC)),
        )
        .with_for_update(read=True, of=[Membership, Workspace])
    )
    if not member:
        raise HTTPException(404, "Workspace not found or no longer available.")
    if member.role not in ("agent", "admin"):
        raise HTTPException(403, "You have read-only access. An Agent or Admin handles changes.")
    item = db.scalar(
        select(Ticket)
        .where(Ticket.workspace_id == workspace_id, Ticket.id == ticket_id)
        .with_for_update()
    )
    if not item:
        raise HTTPException(404, "Ticket not found.")
    if expected_revision is not None and item.revision != expected_revision:
        raise HTTPException(
            409,
            "This ticket changed since you opened it. Load the latest version and review your edits before saving again.",
        )
    return item


def audit(db: Session, item: Ticket, visitor: Identity, action: str, changes: dict):
    db.add(
        AuditEvent(
            workspace_id=item.workspace_id,
            ticket_id=item.id,
            actor_id=visitor.user_id,
            action=action,
            changes=changes,
            created_at=datetime.now(UTC),
        )
    )


@router.get("/workspaces/{workspace_id}/members")
def members(workspace_id: UUID, db: DB, visitor: Visitor):
    membership(db, workspace_id, visitor)
    rows = db.execute(
        text("""SELECT m.user_id, m.role, u.name FROM membership m
        LEFT JOIN "user" u ON u.id=m.user_id
        WHERE m.workspace_id=:w ORDER BY u.name, m.user_id"""),
        {"w": workspace_id},
    )
    return [
        {
            "user_id": r.user_id,
            "role": r.role,
            "name": "You" if r.user_id == visitor.user_id else (r.name or "Workspace member"),
        }
        for r in rows
    ]


@router.patch("/workspaces/{workspace_id}/tickets/{ticket_id}", response_model=TicketDetail)
def change_ticket(
    workspace_id: UUID, ticket_id: UUID, change: HandlingChange, db: DB, visitor: Visitor
):
    item = editable_ticket(db, workspace_id, ticket_id, visitor, change.expected_revision)
    validate_changes(db, item, change)
    changes = {}
    for field in ("status", "priority", "assigned_to", "tags"):
        if field == "tags" and change.tags is None:
            continue
        before, after = getattr(item, field), getattr(change, field)
        if before != after:
            changes[field] = {"before": before, "after": after}
            setattr(item, field, after)
    if changes:
        db.add(
            ApprovalRecord(
                workspace_id=workspace_id,
                ticket_id=ticket_id,
                actor_id=visitor.user_id,
                review_id=None,
                draft_id=None,
                message_id=None,
                content={
                    "actions": changes,
                    "ticket_revision": item.revision,
                    "kind": "explicit_ticket_command",
                },
                created_at=datetime.now(UTC),
            )
        )
        item.revision += 1
        audit(db, item, visitor, "ticket_reopened" if change.reopen else "ticket_updated", changes)
    db.flush()
    result = read_detail(db, item, visitor)
    db.commit()
    return result


@router.post("/workspaces/{workspace_id}/tickets/{ticket_id}/draft", response_model=TicketDetail)
def save_draft(workspace_id: UUID, ticket_id: UUID, change: SaveDraft, db: DB, visitor: Visitor):
    item = editable_ticket(db, workspace_id, ticket_id, visitor, change.expected_revision)
    previous = db.scalar(
        select(DraftRevision)
        .where(DraftRevision.workspace_id == workspace_id, DraftRevision.ticket_id == ticket_id)
        .order_by(DraftRevision.ticket_revision.desc())
        .limit(1)
    )
    if (previous.body if previous else "") != change.body:
        item.revision += 1
        draft = DraftRevision(
            workspace_id=workspace_id,
            ticket_id=ticket_id,
            ticket_revision=item.revision,
            body=change.body,
            generation_id=previous.generation_id if previous else None,
            citation_ids=previous.citation_ids if previous else [],
            created_by=visitor.user_id,
            created_at=datetime.now(UTC),
        )
        db.add(draft)
        db.flush()
        audit(db, item, visitor, "draft_saved", {"draft_revision": str(draft.id)})
    db.flush()
    result = read_detail(db, item, visitor)
    db.commit()
    return result


def validate_changes(db: Session, item: Ticket, change: HandlingChange):
    if item.status == "resolved" and change.status != "resolved" and not change.reopen:
        raise HTTPException(422, "Use Reopen ticket to explicitly reopen a resolved conversation.")
    if change.reopen and not (item.status == "resolved" and change.status == "open"):
        raise HTTPException(422, "Only a resolved ticket can be reopened to open.")
    if change.assigned_to is not None:
        assignee = db.scalar(
            select(Membership)
            .where(
                Membership.workspace_id == item.workspace_id,
                Membership.user_id == change.assigned_to,
            )
            .with_for_update(read=True)
        )
        if not assignee or assignee.role not in ("agent", "admin"):
            raise HTTPException(422, "Assign this ticket to an Agent or Admin in this workspace.")
