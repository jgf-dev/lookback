from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test.db"
    app = create_app(f"sqlite:///{db_path}", initialize_schema=True)
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_endpoint(client: TestClient) -> None:
    response = client.post("/analyze", json={"note": "hello lookback platform"})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"].startswith("Processed note")
    assert 0 <= data["score"] <= 1


def test_create_and_update_item_and_websocket_stream(client: TestClient) -> None:
    with client.websocket_connect("/api/ws/timeline") as websocket:
        target_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_type": "manual_note",
            "raw_content": "Target item",
            "tags": ["target"],
            "inferred_project_task": "Reference target",
            "relationships": [],
            "confidence": 0.7,
            "user_edits": {},
            "provenance": {"captured_by": "keyboard"},
            "enriched_provenance": {"provider": "web"},
        }
        target_response = client.post("/api/items", json=target_payload)
        assert target_response.status_code == 201
        target_item = target_response.json()
        target_event = websocket.receive_json()
        assert target_event["event"] == "created"
        assert target_event["item_id"] == target_item["id"]

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_type": "speech",
            "raw_content": "Discussed roadmap",
            "enriched_content": "Roadmap discussion with milestones",
            "tags": ["planning"],
            "inferred_project_task": "Prepare roadmap draft",
            "relationships": [
                {
                    "target_item_id": target_item["id"],
                    "relationship_type": "depends_on",
                    "confidence": 0.75,
                    "provenance": {"inferred_by": "test"},
                }
            ],
            "confidence": 0.88,
            "user_edits": {"spelling": "none"},
            "provenance": {"captured_by": "microphone"},
            "enriched_provenance": {"provider": "web"},
        }
        create_response = client.post("/api/items", json=payload)
        assert create_response.status_code == 201
        created = create_response.json()
        created_event = websocket.receive_json()
        assert created_event["event"] == "created"
        assert created_event["item_id"] == created["id"]
        assert created["raw_content"] == payload["raw_content"]
        assert created["enriched_content"] == payload["enriched_content"]
        assert created["relationships"][0]["target_item_id"] == target_item["id"]
        assert created["relationships"][0]["relationship_type"] == "depends_on"

        update_response = client.put(
            f"/api/items/{created['id']}",
            json={
                "raw_content": "Updated user note",
                "enriched_content": "Updated automated enrichment",
                "tags": ["planning", "updated"],
                "confidence": 0.95,
                "provenance": {"updated_by": "api_test"},
            },
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        updated_event = websocket.receive_json()
        assert updated_event["event"] == "updated"
        assert updated_event["item_id"] == created["id"]
        assert updated["raw_content"] == "Updated user note"
        assert updated["enriched_content"] == "Updated automated enrichment"
        assert updated["relationships"][0]["target_item_id"] == target_item["id"]
