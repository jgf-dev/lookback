"""initial journal schema

Revision ID: 20260405_0001
Revises:
Create Date: 2026-04-05 00:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260405_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_notes", sa.Text(), nullable=True),
    )

    op.create_table(
        "journal_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("project", sa.String(length=255), nullable=True),
        sa.Column("task", sa.String(length=255), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("embedding_vector", sa.JSON(), nullable=True),
        sa.Column("source_metadata", sa.JSON(), nullable=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("ingestion_sessions.id"), nullable=True),
    )

    op.create_index("ix_journal_entries_created_at", "journal_entries", ["created_at"], unique=False)
    op.create_index("ix_journal_entries_source_type", "journal_entries", ["source_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_journal_entries_source_type", table_name="journal_entries")
    op.drop_index("ix_journal_entries_created_at", table_name="journal_entries")
    op.drop_table("journal_entries")
    op.drop_table("ingestion_sessions")
