from fastapi import APIRouter
from pydantic import BaseModel

from app.services.screenshot_analysis_service import analyze_screenshot

router = APIRouter()


class ScreenshotRequest(BaseModel):
    path: str


@router.post("/analyze")
def analyze(payload: ScreenshotRequest) -> dict[str, str]:
    summary = analyze_screenshot(payload.path)
    return {"summary": summary}
