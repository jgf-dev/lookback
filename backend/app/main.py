# ruff: noqa: E402
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from fastapi import FastAPI
from shared.python.contracts import AnalysisRequest, AnalysisResponse


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application for the lookback backend.
    
    Returns:
        FastAPI: Configured application exposing:
            - GET /health: returns {"status": "ok", "service": "backend"}.
            - POST /analyze: accepts an AnalysisRequest body and returns an AnalysisResponse whose `summary` reports the word count of `note` and whose `score` is min(len(note) / 100, 1.0).
    """
    app = FastAPI(title="lookback-backend", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        """
        Report the basic health status of the service.
        
        Returns:
            dict[str, str]: Mapping with 'status' set to 'ok' and 'service' set to 'backend'.
        """
        return {"status": "ok", "service": "backend"}

    @app.post("/analyze", response_model=AnalysisResponse)
    def analyze(payload: AnalysisRequest) -> AnalysisResponse:
        """
        Create an analysis from the provided request containing a text note.
        
        Parameters:
            payload (AnalysisRequest): Request containing a `note` string to analyze.
        
        Returns:
            AnalysisResponse: Object with `summary` describing the processed note's word count and `score` equal to the note's character-length divided by 100, capped at 1.0.
        """
        summary = f"Processed note with {len(payload.note.split())} words"
        return AnalysisResponse(summary=summary, score=min(len(payload.note) / 100, 1.0))

    return app


app = create_app()
