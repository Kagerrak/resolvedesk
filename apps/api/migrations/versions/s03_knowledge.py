"""Private text knowledge, versioned chunks and durable fixture indexing jobs."""

import sqlalchemy as sa
from alembic import op

revision = "s03_knowledge"
down_revision = "s02_manual_handling"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "knowledge_document",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "id"),
    )
    op.create_index("ix_knowledge_document_workspace_id", "knowledge_document", ["workspace_id"])
    op.create_table(
        "document_version",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("embedding_model", sa.String(), nullable=False),
        sa.Column("published_by", sa.String()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["workspace_id", "document_id"],
            ["knowledge_document.workspace_id", "knowledge_document.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("workspace_id", "id"),
        sa.UniqueConstraint("document_id", "number"),
        sa.CheckConstraint("status IN ('queued','processing','ready','failed','published')"),
    )
    op.create_index("ix_document_version_document_id", "document_version", ["document_id"])
    op.create_table(
        "knowledge_chunk",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("version_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("heading", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id", "version_id"],
            ["document_version.workspace_id", "document_version.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("version_id", "ordinal"),
    )
    op.create_index("ix_knowledge_chunk_version_id", "knowledge_chunk", ["version_id"])
    op.create_table(
        "knowledge_job",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("version_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("lease_token", sa.Uuid()),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("error", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id", "version_id"],
            ["document_version.workspace_id", "document_version.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("status IN ('queued','processing','succeeded','failed')"),
    )


def downgrade():
    for name in ["knowledge_job", "knowledge_chunk", "document_version", "knowledge_document"]:
        op.drop_table(name)
