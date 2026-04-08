from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CapturedItem(Base):
    __tablename__ = "captured_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    inferred_project_task: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_edits: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user_content: Mapped["CapturedItemUserContent"] = relationship(
        back_populates="item", uselist=False, cascade="all, delete-orphan"
    )
    enriched_content: Mapped[list["CapturedItemEnrichedContent"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="CapturedItemEnrichedContent.created_at.asc()",
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
    outgoing_relationships: Mapped[list["ItemRelationship"]] = relationship(
        foreign_keys="ItemRelationship.source_item_id",
        back_populates="source_item",
        cascade="all, delete-orphan",
    )
    incoming_relationships: Mapped[list["ItemRelationship"]] = relationship(
        foreign_keys="ItemRelationship.target_item_id",
        back_populates="target_item",
        cascade="all, delete-orphan",
    )


class CapturedItemUserContent(Base):
    __tablename__ = "captured_item_user_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("captured_items.id"), unique=True, nullable=False
    )
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)

    item: Mapped[CapturedItem] = relationship(back_populates="user_content")


class CapturedItemEnrichedContent(Base):
    __tablename__ = "captured_item_enriched_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("captured_items.id"), nullable=False)
    enriched_content: Mapped[str] = mapped_column(Text, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    item: Mapped[CapturedItem] = relationship(back_populates="enriched_content")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("captured_items.id"), nullable=False)
    attachment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    uri: Mapped[str] = mapped_column(String(500), nullable=False)
    attachment_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    item: Mapped[CapturedItem] = relationship(back_populates="attachments")


class ItemRelationship(Base):
    __tablename__ = "item_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_item_id: Mapped[int] = mapped_column(
        ForeignKey("captured_items.id"), nullable=False, index=True
    )
    target_item_id: Mapped[int] = mapped_column(
        ForeignKey("captured_items.id"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    source_item: Mapped[CapturedItem] = relationship(
        foreign_keys=[source_item_id],
        back_populates="outgoing_relationships",
    )
    target_item: Mapped[CapturedItem] = relationship(
        foreign_keys=[target_item_id],
        back_populates="incoming_relationships",
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("captured_items.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    changes: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserConsent(Base):
    __tablename__ = "user_consent_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    consent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
