from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .identity import Identity
from .models import Membership, Message, Ticket, Workspace


def create_demo(db: Session, visitor: Identity) -> Workspace:
    if not visitor.anonymous:
        raise HTTPException(403, "Demo workspaces require a demo session.")
    # Serialize the same visitor's retries without blocking other visitors.
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:owner, 0))"),
        {"owner": visitor.user_id},
    )
    workspace = db.scalar(select(Workspace).where(Workspace.demo_owner == visitor.user_id))
    if workspace:
        membership(db, workspace.id, visitor)
        return workspace
    now = datetime.now(UTC)
    workspace = Workspace(
        name="Meridian · Demo", demo_owner=visitor.user_id, expires_at=now + timedelta(hours=1)
    )
    db.add(workspace)
    db.flush()
    db.add(Membership(workspace_id=workspace.id, user_id=visitor.user_id, role="agent"))
    ticket = Ticket(
        workspace_id=workspace.id,
        number=1042,
        subject="Help restoring access to our project",
        customer_name="Alex Morgan",
        customer_email="alex@example.com",
        created_at=now,
    )
    db.add(ticket)
    db.flush()
    db.add(
        Message(
            workspace_id=workspace.id,
            ticket_id=ticket.id,
            sender_name=ticket.customer_name,
            sender_email=ticket.customer_email,
            created_at=now,
            body="Hi Meridian team,\n\nI moved a teammate from Admin to Member this morning, and now they can't open our quarterly planning project. They could access it yesterday.\n\nDoes changing their role remove project access? I'd like to get them back in without giving them workspace-wide admin permissions.\n\nThanks,\nAlex",
        )
    )
    db.commit()
    return workspace


def membership(db: Session, workspace_id: UUID, visitor: Identity) -> Membership:
    member = db.scalar(
        select(Membership)
        .join(Workspace)
        .where(
            Membership.workspace_id == workspace_id,
            Membership.user_id == visitor.user_id,
            (Workspace.expires_at.is_(None)) | (Workspace.expires_at > datetime.now(UTC)),
        )
    )
    if not member:
        raise HTTPException(404, "Workspace not found or no longer available.")
    return member


def ticket_in_workspace(db: Session, workspace_id: UUID, ticket_id: UUID) -> Ticket:
    ticket = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.workspace_id == workspace_id)
    )
    if not ticket:
        raise HTTPException(404, "Ticket not found.")
    return ticket
