from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Entry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    source: str = Field(index=True)
    content: str
    project: Optional[str] = None
    task: Optional[str] = None
    context: Optional[str] = None
    metadata_json: Optional[str] = None


class Insight(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    title: str
    description: str
    action: Optional[str] = None
    confidence: float = 0.0


class DailySummary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: date = Field(index=True, unique=True)
    summary_markdown: str
    reviewed_with_user: bool = False