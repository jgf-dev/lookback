"""Shared pytest fixtures for the Lookback backend test suite."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db.models import Entry, Insight  # noqa: F401 – registers table metadata
from app.db.session import get_session
from app.main import app
from app.services.ai_clients import AIClients


# ---------------------------------------------------------------------------
# In-memory SQLite engine shared across all tests in a session
# ---------------------------------------------------------------------------

@pytest.fixture(name='engine', scope='session')
def engine_fixture():
    """Create an in-memory SQLite engine for the full test session."""
    engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name='session')
def session_fixture(engine):
    """Provide a fresh database session for each test, rolling back on teardown."""
    with Session(engine) as session:
        yield session


# ---------------------------------------------------------------------------
# FastAPI TestClient with dependency overrides
# ---------------------------------------------------------------------------

@pytest.fixture(name='client')
def client_fixture(session):
    """Return a TestClient whose DB session is the in-memory fixture session."""

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Mocked AIClients instance
# ---------------------------------------------------------------------------

@pytest.fixture(name='mock_ai_clients')
def mock_ai_clients_fixture(monkeypatch):
    """Replace module-level ai_clients with a lightweight stub."""
    stub = AIClients.__new__(AIClients)
    stub.openai = None
    stub.gemini = None

    # Patch both the module attribute and the import inside main
    import app.services.ai_clients as ai_module
    import app.main as main_module

    monkeypatch.setattr(ai_module, 'ai_clients', stub)
    monkeypatch.setattr(main_module, 'ai_clients', stub)
    return stub