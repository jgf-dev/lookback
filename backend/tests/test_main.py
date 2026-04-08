from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import create_app

app = create_app("sqlite:///./test.db")
client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_endpoint() -> None:
    """
    Verifies the /analyze endpoint processes a note and returns a summary and a normalized score.
    
    Sends a POST to /analyze with a sample note and asserts the response status is 200, the `summary` begins with "Processed note", and `score` is between 0 and 1 inclusive.
    """
    response = client.post("/analyze", json={"note": "hello lookback platform"})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"].startswith("Processed note")
    assert 0 <= data["score"] <= 1


def test_create_and_update_item_and_websocket_stream() -> None:
    """
    Test that creating and updating an item produces the expected HTTP responses and corresponding websocket events.
    
    Sends a POST to create an item, verifies the response is 201 and that the websocket receives a "created" event with the created item's id and matching content, then sends a PUT to update that item, verifies the response is 200 and that the websocket receives an "updated" event with the same item id and the updated content.
    """
    with client.websocket_connect("/api/ws/timeline") as websocket:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_type": "speech",
            "raw_content": "Discussed roadmap",
            "enriched_content": "Roadmap discussion with milestones",
            "tags": ["planning"],
            "inferred_project_task": "Prepare roadmap draft",
            "relationships": [],
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
