from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    note: str = Field(min_length=1, description="User note content to analyze")


class AnalysisResponse(BaseModel):
    summary: str
    score: float = Field(ge=0.0, le=1.0)
