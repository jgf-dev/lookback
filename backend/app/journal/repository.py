from collections.abc import Sequence
from math import sqrt

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.journal.schemas import EntryCreate
from app.models import JournalEntry


class JournalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_entry(self, payload: EntryCreate) -> JournalEntry:
        row = JournalEntry(**payload.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_entries(self, limit: int = 100, offset: int = 0) -> Sequence[JournalEntry]:
        stmt: Select[tuple[JournalEntry]] = (
            select(JournalEntry)
            .order_by(JournalEntry.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return self.db.scalars(stmt).all()

    def search_entries(self, query: str, limit: int = 50) -> Sequence[JournalEntry]:
        token = f"%{query}%"
        stmt: Select[tuple[JournalEntry]] = (
            select(JournalEntry)
            .where(
                or_(
                    JournalEntry.text.ilike(token),
                    JournalEntry.project.ilike(token),
                    JournalEntry.task.ilike(token),
                )
            )
            .order_by(JournalEntry.created_at.desc())
            .limit(limit)
        )
        return self.db.scalars(stmt).all()

    def deep_search_entries(self, vector: list[float], limit: int = 20) -> Sequence[JournalEntry]:
        # SQLite fallback: fetch recent rows and rank in Python.
        # For PostgreSQL + pgvector this can be replaced with server-side vector operators.
        stmt = select(JournalEntry).where(JournalEntry.embedding_vector.is_not(None)).limit(500)
        candidates = self.db.scalars(stmt).all()
        ranked = sorted(
            candidates,
            key=lambda row: cosine_distance(vector, row.embedding_vector or []),
        )
        return ranked[:limit]


def cosine_distance(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 1.0

    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 1.0

    return 1 - dot / (norm_a * norm_b)
