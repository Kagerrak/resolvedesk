from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from .config import settings
from .database import database
from .handling import read_detail
from .handling import router as handling_router
from .identity import Identity, identity
from .inbox import create_demo, membership, ticket_in_workspace
from .knowledge import router as knowledge_router
from .models import Membership, Ticket, Workspace
from .ticket_views import TicketDetail, TicketView

app = FastAPI(title="ResolveDesk", version="0.1.0")
app.include_router(handling_router)
app.include_router(knowledge_router)
DB = Annotated[Session, Depends(database)]
Visitor = Annotated[Identity, Depends(identity)]


class WorkspaceView(BaseModel):
    id: UUID
    name: str
    role: str
    mode: str = "fixture"
    expires_at: datetime | None


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
def tickets(
    workspace_id: UUID,
    db: DB,
    visitor: Visitor,
    q: str = Query(default="", max_length=200),
    status: Literal["all", "open", "pending", "resolved"] = "all",
    assignment: Literal["all", "mine", "unassigned"] = "all",
):

    membership(db, workspace_id, visitor)
    query = select(Ticket).where(Ticket.workspace_id == workspace_id)
    if q.strip():
        query = query.where(
            or_(
                *(
                    column.icontains(q.strip(), autoescape=True)
                    for column in [Ticket.subject, Ticket.customer_name, Ticket.customer_email]
                )
            )
        )
    if status != "all":
        query = query.where(Ticket.status == status)
    if assignment == "mine":
        query = query.where(Ticket.assigned_to == visitor.user_id)
    elif assignment == "unassigned":
        query = query.where(Ticket.assigned_to.is_(None))
    return db.scalars(query.order_by(Ticket.created_at.desc(), Ticket.id)).all()


@app.get("/workspaces/{workspace_id}/tickets/{ticket_id}", response_model=TicketDetail)
def ticket(workspace_id: UUID, ticket_id: UUID, db: DB, visitor: Visitor):
    membership(db, workspace_id, visitor)
    item = ticket_in_workspace(db, workspace_id, ticket_id)
    return read_detail(db, item, visitor)
