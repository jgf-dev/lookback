from fastapi import APIRouter

from app.api import insights, search, screenshots, transcriptions

api_router = APIRouter()
api_router.include_router(transcriptions.router, prefix="/transcriptions", tags=["transcriptions"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(screenshots.router, prefix="/screenshots", tags=["screenshots"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
