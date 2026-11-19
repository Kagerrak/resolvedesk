"""Exact human approval and atomic simulated delivery; no email transport exists here."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .database import database
from .handling import HandlingChange, audit, editable_ticket, read_detail, validate_changes
from .identity import Identity, identity
from .models import (
    ApprovalRecord,
    ApprovalReview,
    DocumentVersion,
    DraftRevision,
    KnowledgeDocument,
    Message,
    RetrievalResult,
    Ticket,
    Workspace,
)
from .ticket_views import TicketDetail

router = APIRouter()
DB = Annotated[Session, Depends(database)]
Visitor = Annotated[Identity, Depends(identity)]


class ReviewRequest(HandlingChange):
    draft_id: UUID


class ApproveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    acknowledge_unverified: bool = False


def knowledge_lock(db: Session, workspace_id: UUID):
    # Serialize publication (including new documents) with the final approval snapshot.
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"published-snapshot:{workspace_id}"},
    )


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def basis(db: Session, item: Ticket, draft: DraftRevision):
    knowledge_lock(db, item.workspace_id)
    messages = db.execute(
        select(Message.id, Message.body, Message.sender_email, Message.created_at)
        .where(Message.workspace_id == item.workspace_id, Message.ticket_id == item.id)
        .order_by(Message.created_at, Message.id)
    ).all()
    versions = db.execute(
        select(
            KnowledgeDocument.id,
            KnowledgeDocument.revision,
            DocumentVersion.id,
            DocumentVersion.content_hash,
        )
        .join(
            DocumentVersion,
            (DocumentVersion.document_id == KnowledgeDocument.id)
            & (DocumentVersion.workspace_id == KnowledgeDocument.workspace_id),
        )
        .where(
            KnowledgeDocument.workspace_id == item.workspace_id,
            KnowledgeDocument.archived.is_(False),
            DocumentVersion.status == "published",
        )
        .order_by(DocumentVersion.id)
    ).all()
    published = {str(row[2]) for row in versions}
    sources = []
    for citation_id in draft.citation_ids:
        result = db.scalar(
            select(RetrievalResult).where(
                RetrievalResult.workspace_id == item.workspace_id,
                RetrievalResult.id == UUID(citation_id),
            )
        )
        if not result or str(result.version_id) not in published:
            raise HTTPException(
                409, "Draft source material changed. Review evidence and save a new draft."
            )
        sources.append({"citation_id": citation_id, "version_id": str(result.version_id)})
    return {
        "ticket_revision": item.revision,
        "conversation_hash": fingerprint([tuple(m) for m in messages]),
        "published_snapshot_hash": fingerprint([tuple(v) for v in versions]),
        "draft_id": str(draft.id),
        "body_hash": fingerprint(draft.body),
        "sources": sources,
    }


def saved_draft(db: Session, item: Ticket):
    return db.scalar(
        select(DraftRevision)
        .where(DraftRevision.workspace_id == item.workspace_id, DraftRevision.ticket_id == item.id)
        .order_by(DraftRevision.ticket_revision.desc())
        .limit(1)
    )


def demo_only(db: Session, item: Ticket):
    workspace = db.get(Workspace, item.workspace_id)
    if not workspace or not workspace.demo_owner or not workspace.expires_at:
        raise HTTPException(
            403, "Simulated delivery is available only in a synthetic demo workspace."
        )


def review_view(review: ApprovalReview):
    return {
        "id": review.id,
        "body": review.body,
        "actions": review.actions,
        "basis": review.basis,
        "warnings": []
        if review.basis["sources"]
        else ["This draft has no supporting citations. Verify every claim before approving."],
        "created_at": review.created_at,
    }


@router.post("/workspaces/{workspace_id}/tickets/{ticket_id}/approval-reviews")
def create_review(
    workspace_id: UUID, ticket_id: UUID, change: ReviewRequest, db: DB, visitor: Visitor
):
    item = editable_ticket(db, workspace_id, ticket_id, visitor, change.expected_revision)
    demo_only(db, item)
    validate_changes(db, item, change)
    draft = saved_draft(db, item)
    if not draft or draft.id != change.draft_id or not draft.body.strip():
        raise HTTPException(409, "Save and review the latest nonempty draft before approving.")
    if db.scalar(
        select(ApprovalRecord.id).where(
            ApprovalRecord.workspace_id == workspace_id, ApprovalRecord.draft_id == draft.id
        )
    ):
        raise HTTPException(
            409, "This draft already has a recorded demo reply. Save a new revision."
        )
    actions = {
        field: {"before": getattr(item, field), "after": getattr(change, field)}
        for field in ("status", "priority", "assigned_to", "tags")
        if getattr(change, field) is not None or field == "assigned_to"
    }
    actions = {k: v for k, v in actions.items() if v["before"] != v["after"]}
    review = ApprovalReview(
        workspace_id=workspace_id,
        ticket_id=ticket_id,
        draft_id=draft.id,
        body=draft.body,
        actions=actions,
        basis=basis(db, item, draft),
        created_by=visitor.user_id,
        created_at=datetime.now(UTC),
    )
    db.add(review)
    db.flush()
    result = review_view(review)
    db.commit()
    return result


@router.post(
    "/workspaces/{workspace_id}/tickets/{ticket_id}/approval-reviews/{review_id}/approve",
    response_model=TicketDetail,
)
def approve(
    workspace_id: UUID,
    ticket_id: UUID,
    review_id: UUID,
    command: ApproveRequest,
    db: DB,
    visitor: Visitor,
):
    # Access and ticket serialization precede idempotent receipt lookup. A Viewer cannot replay it.
    item = editable_ticket(db, workspace_id, ticket_id, visitor, None)
    review = db.scalar(
        select(ApprovalReview).where(
            ApprovalReview.workspace_id == workspace_id,
            ApprovalReview.ticket_id == ticket_id,
            ApprovalReview.id == review_id,
        )
    )
    if not review or review.created_by != visitor.user_id:
        raise HTTPException(404, "Approval review not found.")
    existing = db.scalar(select(ApprovalRecord).where(ApprovalRecord.review_id == review_id))
    if existing:
        result = read_detail(db, item, visitor)
        db.commit()
        return result
    demo_only(db, item)
    draft = saved_draft(db, item)
    if not draft or basis(db, item, draft) != review.basis or draft.body != review.body:
        raise HTTPException(
            409,
            "The draft, conversation or source material changed. Review again before approving.",
        )
    if not review.basis["sources"] and not command.acknowledge_unverified:
        raise HTTPException(422, "Confirm that you reviewed this uncited draft before approving.")
    if db.scalar(
        select(ApprovalRecord.id).where(
            ApprovalRecord.workspace_id == workspace_id, ApprovalRecord.draft_id == draft.id
        )
    ):
        raise HTTPException(409, "This draft already has a recorded demo reply.")
    values = {field: changes["after"] for field, changes in review.actions.items()}
    change = HandlingChange(
        expected_revision=item.revision,
        status=values.get("status", item.status),
        priority=values.get("priority", item.priority),
        assigned_to=values.get("assigned_to", item.assigned_to),
        tags=values.get("tags", item.tags),
        reopen=item.status == "resolved" and values.get("status") == "open",
    )
    validate_changes(db, item, change)
    now = datetime.now(UTC)
    message = Message(
        workspace_id=workspace_id,
        ticket_id=ticket_id,
        sender_name="Support team",
        sender_email="support@example.com",
        body=review.body,
        kind="simulated_reply",
        created_at=now,
    )
    db.add(message)
    db.flush()
    record = ApprovalRecord(
        workspace_id=workspace_id,
        ticket_id=ticket_id,
        review_id=review.id,
        draft_id=draft.id,
        message_id=message.id,
        actor_id=visitor.user_id,
        content={"body": review.body, "actions": review.actions, "basis": review.basis},
        created_at=now,
    )
    db.add(record)
    db.flush()
    for field, values in review.actions.items():
        setattr(item, field, values["after"])
    item.revision += 1
    audit(
        db,
        item,
        visitor,
        "demo_reply_recorded",
        {
            "draft_revision": str(draft.id),
            "approval_id": str(record.id),
            "delivery": "simulated; no email sent",
        },
    )
    if review.actions:
        audit(db, item, visitor, "ticket_updated", review.actions)
    db.flush()
    result = read_detail(db, item, visitor)
    db.commit()
    return result
