"""Original private PDF bytes and page-aware source passages."""

import sqlalchemy as sa
from alembic import op

revision = "s04_pdf_sources"
down_revision = "s03_knowledge"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("document_version", sa.Column("source_bytes", sa.LargeBinary(), nullable=True))
    op.add_column("document_version", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column("knowledge_chunk", sa.Column("page_number", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "positive_source_page", "knowledge_chunk", "page_number IS NULL OR page_number > 0"
    )


def downgrade():
    op.drop_constraint("positive_source_page", "knowledge_chunk", type_="check")
    op.drop_column("knowledge_chunk", "page_number")
    op.drop_column("document_version", "page_count")
    op.drop_column("document_version", "source_bytes")
