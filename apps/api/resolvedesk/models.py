from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, UniqueConstraint
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
    revision: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("workspace_id", "id"),
        UniqueConstraint("workspace_id", "number"),
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
