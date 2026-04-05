from fastapi import FastAPI

from app.api.routes import router
from app.db import Base, engine

app = FastAPI(title="Lookback Backend")
app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    # Local-dev convenience. Production should rely on Alembic migrations.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
