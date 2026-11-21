"""Remove only expired, explicitly tagged public demos; preserve local work and monthly spend."""

from datetime import UTC, datetime

from sqlalchemy import select, text

from .models import EvaluationRun, GenerationRun, Membership, Workspace


def cleanup(db, limit=50):
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('public-demo-capacity',0))"))
    now = datetime.now(UTC)
    rows = db.scalars(
        select(Workspace)
        .where(
            Workspace.public_demo.is_(True),
            Workspace.demo_owner.is_not(None),
            Workspace.expires_at <= now,
        )
        .order_by(Workspace.expires_at, Workspace.id)
        .limit(limit)
        .with_for_update(skip_locked=True)
    ).all()
    deleted, users = 0, 0
    for workspace in rows:
        # Public deployment never dispatches paid jobs. Preserve an anomalous ledger for review.
        if db.scalar(
            select(GenerationRun.id)
            .where(GenerationRun.workspace_id == workspace.id, GenerationRun.mode != "fixture")
            .limit(1)
        ):
            continue
        for run in db.scalars(
            select(EvaluationRun).where(EvaluationRun.workspace_id == workspace.id)
        ):
            if run.probe_workspace_id:
                probe = db.get(Workspace, run.probe_workspace_id)
                if (
                    probe
                    and probe.name == "Synthetic private evaluation probe"
                    and not probe.demo_owner
                    and probe.expires_at == workspace.expires_at
                ):
                    db.delete(probe)
        owner = workspace.demo_owner
        db.delete(workspace)
        db.flush()
        deleted += 1
        if not db.scalar(
            select(Membership.workspace_id).where(Membership.user_id == owner).limit(1)
        ):
            result = db.execute(
                text(
                    'DELETE FROM "user" WHERE id=:owner AND "isAnonymous"=true AND NOT EXISTS (SELECT 1 FROM workspace WHERE demo_owner=:owner)'
                ),
                {"owner": owner},
            )
            users += result.rowcount
    return {"deleted_workspaces": deleted, "deleted_anonymous_users": users}
