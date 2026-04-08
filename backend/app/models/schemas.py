from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RelationshipCreate(BaseModel):
    target_item_id: int
    relationship_type: str
    confidence: float | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)


class CapturedItemBase(BaseModel):
    timestamp: datetime
    source_type: str
    tags: list[str] = Field(default_factory=list)
    inferred_project_task: str | None = None
    relationships: list[RelationshipCreate] = Field(default_factory=list)
    confidence: float | None = None
    user_edits: dict[str, Any] | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)


class CapturedItemCreate(CapturedItemBase):
    raw_content: str
    enriched_content: str | None = None
    enriched_provenance: dict[str, Any] = Field(default_factory=dict)


class CapturedItemUpdate(BaseModel):
    raw_content: str | None = None
    enriched_content: str | None = None
    tags: list[str] | None = None
    confidence: float | None = None
    user_edits: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None


class CapturedItemRead(CapturedItemBase):
    id: int
    raw_content: str
    enriched_content: str | None = None
