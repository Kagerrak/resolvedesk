"""Record ranking parameters alongside persisted retrieval provenance."""

import sqlalchemy as sa
from alembic import op

revision = "s05_ranking"
down_revision = "s05_retrieval"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "retrieval_run",
        sa.Column(
            "ranking",
            sa.JSON(),
            nullable=False,
            server_default='{"method":"exact-cosine-v1","limit":5,"max_distance":0.65}',
        ),
    )
    op.alter_column("retrieval_run", "ranking", server_default=None)


def downgrade():
    op.drop_column("retrieval_run", "ranking")
