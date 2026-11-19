"""Shared serialization boundary for publication and exact human approval."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def lock_snapshot(db: Session, workspace_id: UUID):
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"published-snapshot:{workspace_id}"},
    )
