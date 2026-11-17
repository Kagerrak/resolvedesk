"""Grant Admin to an existing synthetic local demo only; never provisions live access."""

import argparse
from datetime import UTC, datetime
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import select

from .config import settings
from .database import SessionLocal
from .models import Membership, Workspace


def grant(workspace_id: UUID):
    if urlparse(settings.database_url).hostname not in (
        "localhost",
        "127.0.0.1",
        "::1",
    ) or urlparse(settings.app_origin).hostname not in ("localhost", "127.0.0.1", "::1"):
        raise SystemExit("This command is restricted to a local database and local app origin.")
    with SessionLocal() as db:
        workspace = db.get(Workspace, workspace_id)
        if (
            not workspace
            or not workspace.demo_owner
            or not workspace.expires_at
            or workspace.expires_at <= datetime.now(UTC)
        ):
            raise SystemExit(
                "Use an active synthetic demo workspace. Live workspaces are not eligible."
            )
        member = db.scalar(
            select(Membership)
            .where(
                Membership.workspace_id == workspace_id, Membership.user_id == workspace.demo_owner
            )
            .with_for_update()
        )
        if not member:
            raise SystemExit("Demo owner membership not found.")
        member.role = "admin"
        db.commit()
    print("Local synthetic workspace Admin access enabled. Reload the application.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace_id", type=UUID)
    grant(parser.parse_args().workspace_id)
