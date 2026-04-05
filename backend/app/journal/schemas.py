from datetime import datetime

from pydantic import BaseModel, Field


class EntryCreate(BaseModel):
    text: str
    source_type: str = "audio"
    project: str | None = None
    task: str | None = None
    tags: list[str] | None = None
    embedding_vector: list[float] | None = None
    source_metadata: dict = Field(default_factory=dict)
    session_id: int | None = None


class EntryRead(BaseModel):
    id: int
    text: str
    created_at: datetime
    source_type: str
    project: str | None
    task: str | None
    tags: list[str] | None
    embedding_vector: list[float] | None
    source_metadata: dict | None
    session_id: int | None

    model_config = {"from_attributes": True}
