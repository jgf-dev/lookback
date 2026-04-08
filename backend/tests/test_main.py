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


def test_health_service_field() -> None:
    response = client.get("/health")
    assert response.json()["service"] == "backend"


def test_health_response_only_expected_keys() -> None:
    response = client.get("/health")
    data = response.json()
    assert set(data.keys()) == {"status", "service"}


def test_analyze_single_word_note() -> None:
    response = client.post("/analyze", json={"note": "hello"})
    assert response.status_code == 200
    data = response.json()
    assert "1 words" in data["summary"]


def test_analyze_word_count_reflected_in_summary() -> None:
    response = client.post("/analyze", json={"note": "one two three four five"})
    assert response.status_code == 200
    assert "5 words" in response.json()["summary"]


def test_analyze_score_formula_short_note() -> None:
    note = "hi"
    response = client.post("/analyze", json={"note": note})
    assert response.status_code == 200
    expected_score = len(note) / 100
    assert response.json()["score"] == expected_score


def test_analyze_score_capped_at_one_for_long_note() -> None:
    note = "a" * 200
    response = client.post("/analyze", json={"note": note})
    assert response.status_code == 200
    assert response.json()["score"] == 1.0


def test_analyze_score_exactly_one_at_100_chars() -> None:
    note = "a" * 100
    response = client.post("/analyze", json={"note": note})
    assert response.status_code == 200
    assert response.json()["score"] == 1.0


def test_analyze_score_below_one_for_short_note() -> None:
    note = "short"
    response = client.post("/analyze", json={"note": note})
    assert response.status_code == 200
    assert response.json()["score"] < 1.0


def test_analyze_empty_note_returns_422() -> None:
    response = client.post("/analyze", json={"note": ""})
    assert response.status_code == 422


def test_analyze_missing_note_field_returns_422() -> None:
    response = client.post("/analyze", json={})
    assert response.status_code == 422


def test_analyze_response_has_summary_and_score_keys() -> None:
    response = client.post("/analyze", json={"note": "test note"})
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "score" in data


def test_analyze_score_in_range_for_various_inputs() -> None:
    for note in ["x", "word " * 10, "a" * 99, "a" * 101]:
        response = client.post("/analyze", json={"note": note})
        assert response.status_code == 200
        score = response.json()["score"]
        assert 0.0 <= score <= 1.0, f"Score out of range for note length {len(note)}"


def test_analyze_note_with_only_whitespace_words_counted() -> None:
    # A note with multiple spaces still splits into words
    response = client.post("/analyze", json={"note": "one  two  three"})
    assert response.status_code == 200
    # Python str.split() ignores extra whitespace, yields 3 words
    assert "3 words" in response.json()["summary"]


def test_health_get_method_only() -> None:
    # POST to /health should return 405
    response = client.post("/health")
    assert response.status_code == 405


def test_analyze_post_method_only() -> None:
    # GET to /analyze should return 405
    response = client.get("/analyze")
    assert response.status_code == 405