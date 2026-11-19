"""Content-free recovery timeline and source deletion tombstones."""

import sqlalchemy as sa
from alembic import op

revision = "s10_activity"
down_revision = "s07_approval"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("knowledge_document", sa.Column("deleted_at", sa.DateTime(timezone=True)))
    op.create_table(
        "operation_event",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("operation_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('indexing','source')"),
    )
    op.create_index("ix_operation_event_workspace_id", "operation_event", ["workspace_id"])
    op.create_index("ix_operation_event_operation_id", "operation_event", ["operation_id"])


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM operation_event")):
        raise RuntimeError("Preserve operational history; downgrade requires an empty timeline.")
    if op.get_bind().scalar(
        sa.text("SELECT count(*) FROM knowledge_document WHERE deleted_at IS NOT NULL")
    ):
        raise RuntimeError("Preserve deletion tombstones.")
    op.drop_table("operation_event")
    op.drop_column("knowledge_document", "deleted_at")
