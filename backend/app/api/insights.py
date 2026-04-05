from fastapi import APIRouter
from pydantic import BaseModel

from app.services.insights_service import generate_day_review

router = APIRouter()


class DayReviewRequest(BaseModel):
    date: str


@router.post("/day-review")
def day_review(payload: DayReviewRequest) -> dict[str, object]:
    review = generate_day_review(payload.date)
    return review
