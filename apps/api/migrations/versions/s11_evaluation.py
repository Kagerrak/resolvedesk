"""Versioned, workspace-scoped evaluation records and disclosed reviews."""

import sqlalchemy as sa
from alembic import op

revision = "s11_evaluation"
down_revision = "s10_activity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "evaluation_run",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("dataset_version", sa.String(), nullable=False),
        sa.Column("dataset_hash", sa.String(), nullable=False),
        sa.Column("split", sa.String(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("prompt_version", sa.String()),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_map", sa.JSON(), nullable=False),
        sa.Column(
            "probe_workspace_id", sa.Uuid(), sa.ForeignKey("workspace.id", ondelete="SET NULL")
        ),
        sa.Column("probe_marker", sa.String()),
        sa.Column("prepared", sa.Boolean(), nullable=False),
        sa.Column("lease_token", sa.Uuid()),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("error", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("workspace_id", "id"),
        sa.UniqueConstraint("workspace_id", "request_id"),
        sa.CheckConstraint("mode IN ('fixture','deepseek_sample')"),
        sa.CheckConstraint("split IN ('tuning','all')"),
        sa.CheckConstraint("method IN ('exact-cosine-v1','bm25-v1')"),
        sa.CheckConstraint(
            "status IN ('queued','preparing','running','completed','cancelled','failed')"
        ),
    )
    op.create_index("ix_evaluation_run_workspace_id", "evaluation_run", ["workspace_id"])
    op.create_table(
        "evaluation_case",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("case_key", sa.String(), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("retrieval", sa.JSON()),
        sa.Column("fixture_output", sa.JSON()),
        sa.Column("generation_id", sa.Uuid()),
        sa.Column("provider_output", sa.JSON()),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("error", sa.String()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["workspace_id", "run_id"],
            ["evaluation_run.workspace_id", "evaluation_run.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "ticket_id"], ["ticket.workspace_id", "ticket.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "ticket_id", "generation_id"],
            ["generation_run.workspace_id", "generation_run.ticket_id", "generation_run.id"],
        ),
        sa.UniqueConstraint("run_id", "case_key"),
        sa.UniqueConstraint("workspace_id", "run_id", "id"),
        sa.CheckConstraint("status IN ('pending','running','completed','failed')"),
        sa.CheckConstraint("attempts >= 0 AND attempts <= 3"),
    )
    op.create_index("ix_evaluation_case_run_id", "evaluation_case", ["run_id"])
    op.create_table(
        "evaluation_review",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("output_hash", sa.String(), nullable=False),
        sa.Column("reviewer_id", sa.String(), nullable=False),
        sa.Column("reviewer_kind", sa.String(), nullable=False),
        sa.Column("verdict", sa.String(), nullable=False),
        sa.Column("note", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id", "run_id", "case_id"],
            ["evaluation_case.workspace_id", "evaluation_case.run_id", "evaluation_case.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("workspace_id", "request_id"),
        sa.CheckConstraint("reviewer_kind IN ('agent_rubric','member')"),
        sa.CheckConstraint(
            "verdict IN ('supported','unsupported','safe_escalation','conservative_escalation')"
        ),
    )
    op.create_index("ix_evaluation_review_case_id", "evaluation_review", ["case_id"])


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM evaluation_run")):
        raise RuntimeError(
            "Preserve evaluation provenance; downgrade requires an empty evaluation ledger."
        )
    op.drop_table("evaluation_review")
    op.drop_table("evaluation_case")
    op.drop_table("evaluation_run")
