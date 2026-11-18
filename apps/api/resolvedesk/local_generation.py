"""Explicit local-only live drafting of synthetic data; never enables public paid access."""

import argparse
from datetime import UTC, datetime
from urllib.parse import urlparse
from uuid import UUID, uuid4

from sqlalchemy import select

from .config import settings
from .database import SessionLocal
from .generation import Generate, queue, run_once
from .identity import Identity
from .models import Membership, RetrievalRun, Ticket, Workspace


def execute(workspace_id: UUID, ticket_id: UUID):
    if any(
        urlparse(value).hostname not in ("localhost", "127.0.0.1", "::1")
        for value in [settings.database_url, settings.app_origin, settings.auth_url]
    ):
        raise SystemExit(
            "Live evaluation command requires local database and application endpoints."
        )
    if not settings.live_ai_enabled or not settings.openai_api_key:
        raise SystemExit(
            "Configure local OPENAI_API_KEY and LIVE_AI_ENABLED only after usage-control verification."
        )
    with SessionLocal() as db:
        workspace = db.get(Workspace, workspace_id)
        if (
            not workspace
            or not workspace.demo_owner
            or not workspace.expires_at
            or workspace.expires_at <= datetime.now(UTC)
        ):
            raise SystemExit("Use an active synthetic demo workspace.")
        member = db.get(Membership, (workspace_id, workspace.demo_owner))
        if not member or member.role != "admin":
            raise SystemExit("An active local demo Admin is required.")
        ticket = db.scalar(
            select(Ticket).where(Ticket.workspace_id == workspace_id, Ticket.id == ticket_id)
        )
        retrieval = db.scalar(
            select(RetrievalRun)
            .where(RetrievalRun.workspace_id == workspace_id, RetrievalRun.ticket_id == ticket_id)
            .order_by(RetrievalRun.created_at.desc())
            .limit(1)
        )
        if not ticket or not retrieval:
            raise SystemExit("Open this workspace ticket and retrieve evidence first.")
        run = queue(
            db,
            workspace_id,
            ticket_id,
            Generate(
                expected_revision=ticket.revision, retrieval_id=retrieval.id, request_id=uuid4()
            ),
            Identity(workspace.demo_owner, True),
            mode="openai",
        )
        run_id = run.id
        db.commit()
    # The normal worker performs atomic spending reservation before contacting OpenAI.
    run_once()
    print("Live run queued/processed:", run_id, "Inspect the ticket before relying on the draft.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace_id", type=UUID)
    parser.add_argument("ticket_id", type=UUID)
    execute(**vars(parser.parse_args()))
