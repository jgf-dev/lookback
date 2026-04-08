# ruff: noqa: E402
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from fastapi import FastAPI
from shared.python.contracts import AnalysisRequest, AnalysisResponse

from app.api.routes import router as api_router
from app.api.timeline import TimelineBroadcaster
from app.db.base import Base
from app.db.session import create_engine_and_session_factory
from app.models import db_models  # noqa: F401


def create_app(database_url: str = "sqlite:///./lookback.db") -> FastAPI:
    app = FastAPI(title="lookback-backend", version="0.1.0")

    engine, session_factory = create_engine_and_session_factory(database_url)
    app.state.session_factory = session_factory
    app.state.timeline = TimelineBroadcaster()
    Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "backend"}

    @app.post("/analyze", response_model=AnalysisResponse)
    def analyze(payload: AnalysisRequest) -> AnalysisResponse:
        summary = f"Processed note with {len(payload.note.split())} words"
        return AnalysisResponse(summary=summary, score=min(len(payload.note) / 100, 1.0))

    app.include_router(api_router)
    return app


app = create_app()
