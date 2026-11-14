from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .config import settings
from .database import database
from .identity import Identity, identity
from .inbox import create_demo, membership, ticket_in_workspace
from .models import Membership, Message, Ticket, Workspace

app = FastAPI(title="ResolveDesk", version="0.1.0")
DB = Annotated[Session, Depends(database)]
Visitor = Annotated[Identity, Depends(identity)]


class WorkspaceView(BaseModel):
    id: UUID
    name: str
    role: str
    mode: str = "fixture"
    expires_at: datetime | None


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
    revision: int
    created_at: datetime


class TicketDetail(TicketView):
    messages: list[MessageView]


@app.middleware("http")
async def request_policy(request: Request, call_next):
    from fastapi.responses import JSONResponse

    if (
        request.method not in ("GET", "HEAD", "OPTIONS")
        and request.headers.get("origin") != settings.app_origin
    ):
        return JSONResponse({"detail": "Request origin not allowed"}, status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/health")
def health(db: DB):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "mode": "fixture"}


@app.post("/demo", response_model=WorkspaceView)
def demo(db: DB, visitor: Visitor):
    if not settings.demo_enabled:
        raise HTTPException(403, "Demo creation is disabled.")
    workspace = create_demo(db, visitor)
    return WorkspaceView(
        id=workspace.id,
        name=workspace.name,
        role=membership(db, workspace.id, visitor).role,
        expires_at=workspace.expires_at,
    )


@app.get("/workspaces", response_model=list[WorkspaceView])
def workspaces(db: DB, visitor: Visitor):
    rows = db.execute(
        select(Workspace, Membership.role)
        .join(Membership)
        .where(
            Membership.user_id == visitor.user_id,
            Workspace.expires_at.is_(None) | (Workspace.expires_at > datetime.now(UTC)),
        )
        .order_by(Workspace.name)
    ).all()
    return [
        WorkspaceView(id=w.id, name=w.name, role=role, expires_at=w.expires_at) for w, role in rows
    ]


@app.get("/workspaces/{workspace_id}/tickets", response_model=list[TicketView])
def tickets(workspace_id: UUID, db: DB, visitor: Visitor):
    membership(db, workspace_id, visitor)
    return db.scalars(
        select(Ticket).where(Ticket.workspace_id == workspace_id).order_by(Ticket.created_at.desc())
    ).all()


@app.get("/workspaces/{workspace_id}/tickets/{ticket_id}", response_model=TicketDetail)
def ticket(workspace_id: UUID, ticket_id: UUID, db: DB, visitor: Visitor):
    membership(db, workspace_id, visitor)
    item = ticket_in_workspace(db, workspace_id, ticket_id)
    messages = db.scalars(
        select(Message)
        .where(
            Message.workspace_id == workspace_id,
            Message.ticket_id == ticket_id,
        )
        .order_by(Message.created_at, Message.id)
    ).all()
    return TicketDetail(
        **TicketView.model_validate(item).model_dump(),
        messages=[MessageView.model_validate(m) for m in messages],
    )
