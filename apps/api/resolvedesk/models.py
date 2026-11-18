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


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_document"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspace.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str]
    archived: Mapped[bool] = mapped_column(default=False)
    revision: Mapped[int] = mapped_column(default=1)
    created_by: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("workspace_id", "id"),)


class DocumentVersion(Base):
    __tablename__ = "document_version"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    document_id: Mapped[UUID] = mapped_column(index=True)
    number: Mapped[int] = mapped_column(default=1)
    filename: Mapped[str]
    content: Mapped[str]  # Private PostgreSQL storage; never exposed as a static asset.
    content_hash: Mapped[str]
    status: Mapped[str] = mapped_column(default="queued")
    embedding_model: Mapped[str] = mapped_column(default="fixture-hash-v1")
    published_by: Mapped[str | None]
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "document_id"],
            ["knowledge_document.workspace_id", "knowledge_document.id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("workspace_id", "id"),
        UniqueConstraint("document_id", "number"),
        CheckConstraint("status IN ('queued','processing','ready','failed','published')"),
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunk"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    version_id: Mapped[UUID] = mapped_column(index=True)
    ordinal: Mapped[int]
    heading: Mapped[str]
    content: Mapped[str]
    embedding: Mapped[list] = mapped_column(JSON)
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "version_id"],
            ["document_version.workspace_id", "document_version.id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("version_id", "ordinal"),
    )


class KnowledgeJob(Base):
    __tablename__ = "knowledge_job"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    version_id: Mapped[UUID] = mapped_column(unique=True)
    status: Mapped[str] = mapped_column(default="queued")
    attempts: Mapped[int] = mapped_column(default=0)
    lease_token: Mapped[UUID | None]
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "version_id"],
            ["document_version.workspace_id", "document_version.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("status IN ('queued','processing','succeeded','failed')"),
    )
