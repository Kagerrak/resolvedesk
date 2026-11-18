from datetime import datetime
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
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
    generation_id: Mapped[UUID | None]
    citation_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_by: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "ticket_id"], ["ticket.workspace_id", "ticket.id"], ondelete="CASCADE"
        ),
        UniqueConstraint("ticket_id", "ticket_revision"),
        UniqueConstraint("workspace_id", "ticket_id", "id"),
        ForeignKeyConstraint(
            ["workspace_id", "ticket_id", "generation_id"],
            ["generation_run.workspace_id", "generation_run.ticket_id", "generation_run.id"],
            name="draft_generation_source",
        ),
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
    source_bytes: Mapped[bytes | None]
    page_count: Mapped[int | None]
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
    page_number: Mapped[int | None]
    ordinal: Mapped[int]
    heading: Mapped[str]
    content: Mapped[str]
    embedding: Mapped[list] = mapped_column(Vector(64))
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "version_id"],
            ["document_version.workspace_id", "document_version.id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("version_id", "ordinal"),
        UniqueConstraint("workspace_id", "version_id", "id"),
        CheckConstraint("page_number IS NULL OR page_number > 0", name="positive_source_page"),
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


class RetrievalRun(Base):
    __tablename__ = "retrieval_run"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    ticket_id: Mapped[UUID]
    ticket_revision: Mapped[int]
    query: Mapped[str]
    embedding_model: Mapped[str]
    source_versions: Mapped[list] = mapped_column(JSON)
    ranking: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "ticket_id"], ["ticket.workspace_id", "ticket.id"], ondelete="CASCADE"
        ),
        UniqueConstraint("workspace_id", "id"),
        UniqueConstraint("workspace_id", "ticket_id", "id"),
    )


class RetrievalResult(Base):
    __tablename__ = "retrieval_result"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    run_id: Mapped[UUID]
    version_id: Mapped[UUID]
    chunk_id: Mapped[UUID]
    rank: Mapped[int]
    distance: Mapped[float]
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "run_id"],
            ["retrieval_run.workspace_id", "retrieval_run.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "version_id"],
            ["document_version.workspace_id", "document_version.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "version_id", "chunk_id"],
            ["knowledge_chunk.workspace_id", "knowledge_chunk.version_id", "knowledge_chunk.id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("run_id", "rank"),
    )


class GenerationRun(Base):
    __tablename__ = "generation_run"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    ticket_id: Mapped[UUID]
    retrieval_id: Mapped[UUID]
    request_id: Mapped[UUID]
    ticket_revision: Mapped[int]
    mode: Mapped[str]
    model: Mapped[str]
    prompt_version: Mapped[str]
    prompt_hash: Mapped[str | None]
    status: Mapped[str] = mapped_column(default="queued")
    error: Mapped[str | None]
    citations: Mapped[list] = mapped_column(JSON, default=list)
    draft_id: Mapped[UUID | None]
    charge_micros: Mapped[int] = mapped_column(default=0)
    usage: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "ticket_id"], ["ticket.workspace_id", "ticket.id"], ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["workspace_id", "ticket_id", "retrieval_id"],
            ["retrieval_run.workspace_id", "retrieval_run.ticket_id", "retrieval_run.id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("workspace_id", "request_id"),
        UniqueConstraint("workspace_id", "ticket_id", "id"),
        ForeignKeyConstraint(
            ["workspace_id", "ticket_id", "draft_id"],
            ["draft_revision.workspace_id", "draft_revision.ticket_id", "draft_revision.id"],
            name="generation_draft_source",
            use_alter=True,
        ),
        CheckConstraint("mode IN ('fixture','openai')"),
        CheckConstraint(
            "status IN ('queued','running','succeeded','escalated','failed','cancelled')"
        ),
        CheckConstraint("charge_micros >= 0"),
    )


class UsageMonth(Base):
    __tablename__ = "usage_month"
    month: Mapped[str] = mapped_column(primary_key=True)
    allocated_micros: Mapped[int] = mapped_column(default=0)
    blocked: Mapped[bool] = mapped_column(default=False)
    __table_args__ = (CheckConstraint("allocated_micros >= 0 AND allocated_micros <= 20000000"),)
