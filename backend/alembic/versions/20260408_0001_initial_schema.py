"""initial persistence schema

Revision ID: 20260408_0001
Revises:
Create Date: 2026-04-08
"""

import sqlalchemy as sa

from alembic import op

revision = "20260408_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create the initial database schema for the application.
    
    Creates tables and indexes required for captured item storage and related data: 
    - captured_items: primary table for captured records with timestamps, source, tags, provenance, and audit timestamps.
    - captured_item_user_content: one-to-one user-provided raw content for a captured item.
    - captured_item_enriched_content: enriched/generated content for a captured item with creation timestamp.
    - attachments: attachments related to captured items with type, URI, and optional metadata.
    - item_relationships: directed relationships between captured items with relationship type, optional confidence, and provenance.
    - audit_logs: action records referencing captured items, actor, change payload, and timestamp.
    - user_consent_records: user consent entries with consent type, granted flag, timestamp, and provenance.
    
    Also creates indexes on captured_items.id and user_consent_records.user_id.
    """
    op.create_table(
        "captured_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("inferred_project_task", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("user_edits", sa.JSON(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_captured_items_id", "captured_items", ["id"])

    op.create_table(
        "captured_item_user_content",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "item_id",
            sa.Integer(),
            sa.ForeignKey("captured_items.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
    )

    op.create_table(
        "captured_item_enriched_content",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("captured_items.id"), nullable=False),
        sa.Column("enriched_content", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("captured_items.id"), nullable=False),
        sa.Column("attachment_type", sa.String(length=50), nullable=False),
        sa.Column("uri", sa.String(length=500), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
    )

    op.create_table(
        "item_relationships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "source_item_id", sa.Integer(), sa.ForeignKey("captured_items.id"), nullable=False
        ),
        sa.Column(
            "target_item_id", sa.Integer(), sa.ForeignKey("captured_items.id"), nullable=False
        ),
        sa.Column("relationship_type", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("captured_items.id"), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("actor", sa.String(length=100), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "user_consent_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("consent_type", sa.String(length=100), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
    )
    op.create_index("ix_user_consent_records_user_id", "user_consent_records", ["user_id"])


def downgrade() -> None:
    """
    Reverts the database schema created by this migration.
    
    Drops the index on user_consent_records.user_id, removes the tables created for user_consent_records, audit_logs, item_relationships, attachments, captured_item_enriched_content, and captured_item_user_content, then drops the index on captured_items.id and finally removes the captured_items table.
    """
    op.drop_index("ix_user_consent_records_user_id", table_name="user_consent_records")
    op.drop_table("user_consent_records")
    op.drop_table("audit_logs")
    op.drop_table("item_relationships")
    op.drop_table("attachments")
    op.drop_table("captured_item_enriched_content")
    op.drop_table("captured_item_user_content")
    op.drop_index("ix_captured_items_id", table_name="captured_items")
    op.drop_table("captured_items")
