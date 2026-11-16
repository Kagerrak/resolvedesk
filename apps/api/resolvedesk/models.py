from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Workspace(Base):
    __tablename__ = "workspace"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str]
    demo_owner: Mapped[str | None] = mapped_column(unique=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Membership(Base):
    __tablename__ = "membership"
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspace.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(primary_key=True)
    role: Mapped[str]
    __table_args__ = (CheckConstraint("role IN ('admin','agent','viewer')"),)


class Ticket(Base):
    __tablename__ = "ticket"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspace.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[int]
    subject: Mapped[str]
    customer_name: Mapped[str]
    customer_email: Mapped[str]
    status: Mapped[str] = mapped_column(default="open")
    priority: Mapped[str] = mapped_column(default="normal")
    assigned_to: Mapped[str | None]
    revision: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        UniqueConstraint("workspace_id", "number"),
        ForeignKeyConstraint(
            ["workspace_id", "assigned_to"],
            ["membership.workspace_id", "membership.user_id"],
            name="ticket_assignee_membership",
        ),
        CheckConstraint("status IN ('open','pending','resolved')"),
        CheckConstraint("priority IN ('low','normal','high','urgent')"),
    )


class Message(Base):
    __tablename__ = "message"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    ticket_id: Mapped[UUID] = mapped_column(index=True)
    sender_name: Mapped[str]
    sender_email: Mapped[str]
    body: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "ticket_id"], ["ticket.workspace_id", "ticket.id"], ondelete="CASCADE"
        ),
    )


class DraftRevision(Base):
    __tablename__ = "draft_revision"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    ticket_id: Mapped[UUID] = mapped_column(index=True)
    ticket_revision: Mapped[int]
    body: Mapped[str]
    created_by: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "ticket_id"], ["ticket.workspace_id", "ticket.id"], ondelete="CASCADE"
        ),
        UniqueConstraint("ticket_id", "ticket_revision"),
    )


class AuditEvent(Base):
    __tablename__ = "audit_event"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    ticket_id: Mapped[UUID] = mapped_column(index=True)
    actor_id: Mapped[str]
    action: Mapped[str]
    changes: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "ticket_id"], ["ticket.workspace_id", "ticket.id"], ondelete="CASCADE"
        ),
    )
