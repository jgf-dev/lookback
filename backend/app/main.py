# ruff: noqa: E402
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from fastapi import FastAPI
from shared.python.contracts import AnalysisRequest, AnalysisResponse


def create_app() -> FastAPI:
    app = FastAPI(title="lookback-backend", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "backend"}

    @app.post("/analyze", response_model=AnalysisResponse)
    def analyze(payload: AnalysisRequest) -> AnalysisResponse:
        summary = f"Processed note with {len(payload.note.split())} words"
        return AnalysisResponse(summary=summary, score=min(len(payload.note) / 100, 1.0))

    return app


app = create_app()
