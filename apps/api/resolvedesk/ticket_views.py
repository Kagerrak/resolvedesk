from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MessageView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    sender_name: str
    sender_email: str
    body: str
    created_at: datetime


class TicketView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    number: int
    subject: str
    customer_name: str
    customer_email: str
    status: str
    priority: str
    assigned_to: str | None
    revision: int
    created_at: datetime


class DraftView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    body: str
    ticket_revision: int
    created_at: datetime


class EventView(BaseModel):
    id: UUID
    actor: str
    action: str
    changes: dict
    created_at: datetime


class TicketDetail(TicketView):
    messages: list[MessageView]
    draft: DraftView | None
    events: list[EventView]
