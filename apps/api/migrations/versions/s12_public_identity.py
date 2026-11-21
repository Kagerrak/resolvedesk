"""Bound public anonymous signups before authentication rows are created."""

import sqlalchemy as sa
from alembic import op

revision = "s12_public_identity"
down_revision = "s12_public_demo"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "public_auth_window",
        sa.Column("hour", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("identities", sa.Integer(), nullable=False),
        sa.CheckConstraint("identities >= 0 AND identities <= 20"),
    )


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM public_auth_window")):
        raise RuntimeError(
            "Preserve public signup capacity; downgrade requires an empty public signup ledger."
        )
    op.drop_table("public_auth_window")
