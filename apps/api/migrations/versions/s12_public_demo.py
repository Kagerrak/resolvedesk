"""Explicit public demo boundaries and bounded durable session counters."""

import sqlalchemy as sa
from alembic import op

revision = "s12_public_demo"
down_revision = "s11_evaluation"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "workspace",
        sa.Column("public_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "demo_quota",
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("writes", sa.Integer(), nullable=False),
        sa.Column("retrievals", sa.Integer(), nullable=False),
        sa.CheckConstraint("writes >= 0 AND writes <= 100"),
        sa.CheckConstraint("retrievals >= 0 AND retrievals <= 30"),
    )
    op.create_table(
        "demo_window",
        sa.Column("hour", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("sessions", sa.Integer(), nullable=False),
        sa.CheckConstraint("sessions >= 0 AND sessions <= 20"),
    )


def downgrade():
    if (
        op.get_bind().scalar(sa.text("SELECT count(*) FROM workspace WHERE public_demo"))
        or op.get_bind().scalar(sa.text("SELECT count(*) FROM demo_window"))
        or op.get_bind().scalar(sa.text("SELECT count(*) FROM demo_quota"))
    ):
        raise RuntimeError(
            "Preserve public demo boundaries; downgrade requires an empty public demo ledger."
        )
    op.drop_table("demo_window")
    op.drop_table("demo_quota")
    op.drop_column("workspace", "public_demo")
