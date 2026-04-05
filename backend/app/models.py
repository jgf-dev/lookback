from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base


class IngestionSession(Base):
    __tablename__ = "ingestion_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    entries: Mapped[list["JournalEntry"]] = relationship(back_populates="session")


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="audio")
    project: Mapped[str | None] = mapped_column(String(255), nullable=True)
    task: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    embedding_vector: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    source_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("ingestion_sessions.id"), nullable=True)

    session: Mapped[IngestionSession | None] = relationship(back_populates="entries")
