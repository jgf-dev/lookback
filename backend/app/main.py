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
    """
    Create and configure the FastAPI application used by the backend.
    
    Parameters:
        database_url (str): SQLAlchemy database URL used to create the engine and session factory (defaults to "sqlite:///./lookback.db").
    
    Returns:
        app (FastAPI): A FastAPI instance with persistence initialized, database tables created, the timeline broadcaster and session factory stored on app.state, health and analyze endpoints registered, and additional routes included from the application's router.
    """
    app = FastAPI(title="lookback-backend", version="0.1.0")

    engine, session_factory = create_engine_and_session_factory(database_url)
    app.state.session_factory = session_factory
    app.state.timeline = TimelineBroadcaster()
    Base.metadata.create_all(bind=engine)

    @app.get("/health")
    def health() -> dict[str, str]:
        """
        Report the application's health status.
        
        Returns:
            dict[str, str]: A mapping with "status" set to "ok" and "service" set to "backend".
        """
        return {"status": "ok", "service": "backend"}

    @app.post("/analyze", response_model=AnalysisResponse)
    def analyze(payload: AnalysisRequest) -> AnalysisResponse:
        """
        Create a brief analysis of the provided note.
        
        Parameters:
            payload (AnalysisRequest): Request containing the note text to analyze; `payload.note` is used.
        
        Returns:
            AnalysisResponse: Contains `summary`, a string stating the number of words in the note, and `score`, a float between 0.0 and 1.0 proportional to the note's character length (capped at 1.0).
        """
        summary = f"Processed note with {len(payload.note.split())} words"
        return AnalysisResponse(summary=summary, score=min(len(payload.note) / 100, 1.0))

    app.include_router(api_router)
    return app


app = create_app()
