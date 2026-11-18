"""Native pgvector passages and persisted workspace-scoped retrieval references."""

from alembic import op
import sqlalchemy as sa

revision = "s05_retrieval"
down_revision = "s04_pdf_sources"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        "ALTER TABLE knowledge_chunk ALTER COLUMN embedding TYPE vector(64) "
        "USING embedding::text::vector(64)"
    )
    op.create_unique_constraint(
        "uq_chunk_source", "knowledge_chunk", ["workspace_id", "version_id", "id"]
    )
    op.create_table(
        "retrieval_run",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_revision", sa.Integer(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("embedding_model", sa.String(), nullable=False),
        sa.Column("source_versions", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id", "ticket_id"], ["ticket.workspace_id", "ticket.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("workspace_id", "id"),
    )
    op.create_table(
        "retrieval_result",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("version_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("distance", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id", "run_id"],
            ["retrieval_run.workspace_id", "retrieval_run.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "version_id"],
            ["document_version.workspace_id", "document_version.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id", "version_id", "chunk_id"],
            ["knowledge_chunk.workspace_id", "knowledge_chunk.version_id", "knowledge_chunk.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("run_id", "rank"),
    )
    op.create_index(
        "ix_retrieval_ticket", "retrieval_run", ["workspace_id", "ticket_id", "created_at"]
    )


def downgrade():
    op.drop_table("retrieval_result")
    op.drop_table("retrieval_run")
    op.drop_constraint("uq_chunk_source", "knowledge_chunk")
    op.execute(
        "ALTER TABLE knowledge_chunk ALTER COLUMN embedding TYPE json USING embedding::text::json"
    )
