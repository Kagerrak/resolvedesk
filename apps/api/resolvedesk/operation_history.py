"""Content-free operational transitions, committed alongside their domain effects."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from .models import OperationEvent


def record(
    db: Session,
    workspace_id: UUID,
    operation_id: UUID,
    kind: str,
    phase: str,
    attempt: int = 0,
    actor_id: str | None = None,
):
    db.add(
        OperationEvent(
            workspace_id=workspace_id,
            operation_id=operation_id,
            kind=kind,
            phase=phase,
            attempt=attempt,
            actor_id=actor_id,
            created_at=datetime.now(UTC),
        )
    )
