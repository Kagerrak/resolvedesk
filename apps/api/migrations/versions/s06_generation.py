"""Durable generation runs and atomic conservative usage allocation."""

import sqlalchemy as sa
from alembic import op

revision = "s06_generation"
down_revision = "s05_ranking"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_retrieval_ticket_source", "retrieval_run", ["workspace_id", "ticket_id", "id"]
    )
    op.create_unique_constraint(
        "uq_draft_ticket_source", "draft_revision", ["workspace_id", "ticket_id", "id"]
    )
    op.create_table(
        "usage_month",
        sa.Column("month", sa.String(), primary_key=True),
        sa.Column("allocated_micros", sa.Integer(), nullable=False),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.CheckConstraint("allocated_micros >= 0 AND allocated_micros <= 20000000"),
    )
    op.create_table(
        "generation_run",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("retrieval_id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_revision", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("prompt_version", sa.String(), nullable=False),
        sa.Column("prompt_hash", sa.String()),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error", sa.String()),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("draft_id", sa.Uuid()),
        sa.Column("charge_micros", sa.Integer(), nullable=False),
        sa.Column("usage", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["workspace_id", "ticket_id"], ["ticket.workspace_id", "ticket.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "ticket_id", "retrieval_id"],
            ["retrieval_run.workspace_id", "retrieval_run.ticket_id", "retrieval_run.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("workspace_id", "request_id"),
        sa.UniqueConstraint("workspace_id", "ticket_id", "id"),
        sa.CheckConstraint("mode IN ('fixture','openai')"),
        sa.CheckConstraint(
            "status IN ('queued','running','succeeded','escalated','failed','cancelled')"
        ),
        sa.CheckConstraint("charge_micros >= 0"),
    )
    op.create_index(
        "ix_generation_ticket", "generation_run", ["workspace_id", "ticket_id", "created_at"]
    )

    op.add_column("draft_revision", sa.Column("generation_id", sa.Uuid()))
    op.add_column(
        "draft_revision", sa.Column("citation_ids", sa.JSON(), nullable=False, server_default="[]")
    )
    op.alter_column("draft_revision", "citation_ids", server_default=None)
    op.create_foreign_key(
        "draft_generation_source",
        "draft_revision",
        "generation_run",
        ["workspace_id", "ticket_id", "generation_id"],
        ["workspace_id", "ticket_id", "id"],
    )
    op.create_foreign_key(
        "generation_draft_source",
        "generation_run",
        "draft_revision",
        ["workspace_id", "ticket_id", "draft_id"],
        ["workspace_id", "ticket_id", "id"],
    )


def downgrade():
    op.drop_constraint("generation_draft_source", "generation_run")
    op.drop_constraint("draft_generation_source", "draft_revision")
    op.drop_column("draft_revision", "citation_ids")
    op.drop_column("draft_revision", "generation_id")
    op.drop_table("generation_run")
    op.drop_table("usage_month")
    op.drop_constraint("uq_draft_ticket_source", "draft_revision")
    op.drop_constraint("uq_retrieval_ticket_source", "retrieval_run")
