from fastapi import APIRouter
from pydantic import BaseModel

from app.services.search_service import augment_search_context

router = APIRouter()


class SearchAugmentationRequest(BaseModel):
    query: str


@router.post("/augment")
def augment(payload: SearchAugmentationRequest) -> dict[str, list[str]]:
    snippets = augment_search_context(payload.query)
    return {"snippets": snippets}
