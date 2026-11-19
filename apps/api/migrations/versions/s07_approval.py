"""Exact reviews, human approvals and simulated delivery receipts."""

import sqlalchemy as sa
from alembic import op

revision = "s07_approval"
down_revision = "s06_deepseek"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ticket", sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column(
        "message", sa.Column("kind", sa.String(), nullable=False, server_default="customer")
    )
    op.create_unique_constraint(
        "uq_message_ownership", "message", ["workspace_id", "ticket_id", "id"]
    )
    op.create_table(
        "approval_review",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("draft_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("actions", sa.JSON(), nullable=False),
        sa.Column("basis", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id", "ticket_id", "draft_id"],
            ["draft_revision.workspace_id", "draft_revision.ticket_id", "draft_revision.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("workspace_id", "ticket_id", "id"),
    )
    op.create_table(
        "approval_record",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("review_id", sa.Uuid()),
        sa.Column("draft_id", sa.Uuid()),
        sa.Column("message_id", sa.Uuid()),
        sa.Column("actor_id", sa.String(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id", "ticket_id"], ["ticket.workspace_id", "ticket.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "ticket_id", "review_id"],
            ["approval_review.workspace_id", "approval_review.ticket_id", "approval_review.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "ticket_id", "draft_id"],
            ["draft_revision.workspace_id", "draft_revision.ticket_id", "draft_revision.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "ticket_id", "message_id"],
            ["message.workspace_id", "message.ticket_id", "message.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("review_id"),
        sa.UniqueConstraint("draft_id"),
        sa.UniqueConstraint("message_id"),
    )


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM approval_record")):
        raise RuntimeError(
            "Preserve approval history; downgrade requires an empty approval ledger."
        )
    op.drop_table("approval_record")
    op.drop_table("approval_review")
    op.drop_constraint("uq_message_ownership", "message")
    op.drop_column("message", "kind")
    op.drop_column("ticket", "tags")
