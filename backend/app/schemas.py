from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class EntryIn(BaseModel):
    source: str
    content: str
    project: Optional[str] = None
    task: Optional[str] = None
    context: Optional[str] = None
    metadata: dict[str, Any] | None = None


class ScreenshotIn(BaseModel):
    image_b64: str
    project: Optional[str] = None
    task: Optional[str] = None
    context: Optional[str] = None


class EntryOut(BaseModel):
    id: int
    created_at: datetime
    source: str
    content: str
    project: Optional[str]
    task: Optional[str]
    context: Optional[str]


class InsightOut(BaseModel):
    id: int
    created_at: datetime
    title: str
    description: str
    action: Optional[str]
    confidence: float
