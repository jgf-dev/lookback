from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_endpoint() -> None:
    response = client.post("/analyze", json={"note": "hello lookback platform"})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"].startswith("Processed note")
    assert 0 <= data["score"] <= 1
