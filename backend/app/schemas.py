import json
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, computed_field


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
    model_config = {'from_attributes': True}

    id: int
    created_at: datetime
    source: str
    content: str
    project: Optional[str]
    task: Optional[str]
    context: Optional[str]
    metadata_json: Optional[str] = None

    @computed_field
    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except (json.JSONDecodeError, TypeError):
                return None
        return None


class InsightOut(BaseModel):
    id: int
    created_at: datetime
    title: str
    description: str
    action: Optional[str]
    confidence: float