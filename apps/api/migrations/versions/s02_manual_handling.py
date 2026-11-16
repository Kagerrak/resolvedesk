"""Manual assignment, draft revisions and handling history."""

import sqlalchemy as sa
from alembic import op

revision = "s02_manual_handling"
down_revision = "2aae1c0ebec0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("ticket", sa.Column("assigned_to", sa.String(), nullable=True))
    op.create_foreign_key(
        "ticket_assignee_membership",
        "ticket",
        "membership",
        ["workspace_id", "assigned_to"],
        ["workspace_id", "user_id"],
    )
    for name, columns in [
        (
            "draft_revision",
            [
                sa.Column("ticket_revision", sa.Integer(), nullable=False),
                sa.Column("body", sa.Text(), nullable=False),
                sa.Column("created_by", sa.String(), nullable=False),
            ],
        ),
        (
            "audit_event",
            [
                sa.Column("actor_id", sa.String(), nullable=False),
                sa.Column("action", sa.String(), nullable=False),
                sa.Column("changes", sa.JSON(), nullable=False),
            ],
        ),
    ]:
        op.create_table(
            name,
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("workspace_id", sa.Uuid(), nullable=False),
            sa.Column("ticket_id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            *columns,
            sa.ForeignKeyConstraint(
                ["workspace_id", "ticket_id"],
                ["ticket.workspace_id", "ticket.id"],
                ondelete="CASCADE",
            ),
        )
        op.create_index(f"ix_{name}_ticket_id", name, ["ticket_id"])
    op.create_unique_constraint(
        "draft_ticket_revision", "draft_revision", ["ticket_id", "ticket_revision"]
    )


def downgrade():
    op.drop_table("audit_event")
    op.drop_table("draft_revision")
    op.drop_constraint("ticket_assignee_membership", "ticket", type_="foreignkey")
    op.drop_column("ticket", "assigned_to")
