from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    enriched_provenance: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] | None = None
    confidence: float | None = None
    user_edits: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None


class CapturedItemRead(CapturedItemBase):
    id: int
    raw_content: str
    enriched_content: str | None = None


# ─── Consent ─────────────────────────────────────────────────────────────────


class ConsentCreate(BaseModel):
    consent_type: str
    granted: bool


class ConsentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    consent_type: str
    granted: bool
    timestamp: datetime


# ─── Audit log ───────────────────────────────────────────────────────────────


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int | None = None
    action: str
    actor: str
    changes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
