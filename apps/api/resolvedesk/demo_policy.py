"""Public synthetic boundaries; no client can raise quotas or enable a paid mode."""

from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import and_, func, select, text, true

from .config import settings
from .models import DemoQuota, DemoWindow, Workspace


def public_scope(visitor):
    return (
        and_(Workspace.public_demo.is_(True), Workspace.demo_owner == visitor.user_id)
        if settings.public_demo_only
        else true()
    )


def reserve_creation(db):
    # This common lock protects both the hourly counter and active-session capacity.
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('public-demo-capacity',0))"))
    now = datetime.now(UTC)
    hour = now.replace(minute=0, second=0, microsecond=0)
    window = db.get(DemoWindow, hour)
    if not window:
        window = DemoWindow(hour=hour, sessions=0)
        db.add(window)
    active = (
        db.scalar(
            select(func.count())
            .select_from(Workspace)
            .where(Workspace.public_demo.is_(True), Workspace.expires_at > now)
        )
        or 0
    )
    if window.sessions >= 20 or active >= 50:
        raise HTTPException(
            429, "The demo is busy. Try again later; existing workspaces remain available."
        )
    window.sessions += 1
    # Counts contain no visitor identifier and need only a short abuse-control history.
    db.execute(
        text("DELETE FROM demo_window WHERE hour < :cutoff"), {"cutoff": hour - timedelta(days=2)}
    )


def reserve_action(db, workspace_id, kind: Literal["writes", "retrievals"]):
    workspace = db.get(Workspace, workspace_id)
    if not workspace or not workspace.public_demo:
        return
    quota = db.scalar(
        select(DemoQuota)
        .where(DemoQuota.workspace_id == workspace_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not quota:
        raise HTTPException(503, "Demo limits are unavailable. Saved work remains safe.")
    limit = 100 if kind == "writes" else 30
    if getattr(quota, kind) >= limit:
        raise HTTPException(
            429,
            "This demo has reached its activity limit. You can still inspect saved conversations, evidence and history.",
        )
    setattr(quota, kind, getattr(quota, kind) + 1)


def description():
    return {
        "public_demo": settings.public_demo_only,
        "generation_mode": "fixture",
        "session_minutes": 60,
        "generation_limit": 10,
        "retrieval_limit": 30,
        "write_limit": 100,
        "new_sessions_per_hour": 20,
        "active_session_limit": 50,
        "cleanup": "Access ends after one hour. Expired public demo content is removed on new visits and by scheduled daily cleanup.",
        "connections": "No real mailbox connection or paid AI request is enabled in the public demo.",
    }
