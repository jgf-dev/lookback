"""Tests for the AI provider adapters and their fallback behaviour.

All tests run without real API keys; provider calls are either expected to raise
``ProviderUnavailableError`` (fallback path) or are monkey-patched with lightweight
mock objects to exercise the happy path without making network calls.
"""

import io
import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.providers.config import (
    ProviderUnavailableError,
    get_gemini_api_key,
    get_openai_api_key,
)
from app.services.enrichment.pipeline import enrich_with_context, enrich_with_screenshot
from app.services.ingestion.pipeline import ingest_audio


# ─── config.py ────────────────────────────────────────────────────────────────


def test_get_openai_api_key_raises_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ProviderUnavailableError, match="OPENAI_API_KEY"):
        get_openai_api_key()


def test_get_openai_api_key_raises_when_env_blank(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "   ")
    with pytest.raises(ProviderUnavailableError, match="OPENAI_API_KEY"):
        get_openai_api_key()


def test_get_openai_api_key_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    assert get_openai_api_key() == "sk-test-key"


def test_get_gemini_api_key_raises_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ProviderUnavailableError, match="GEMINI_API_KEY"):
        get_gemini_api_key()


def test_get_gemini_api_key_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    assert get_gemini_api_key() == "gemini-test-key"


# ─── openai_adapter.py — fallback (no key) ────────────────────────────────────


def test_transcribe_audio_raises_when_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from app.services.providers.openai_adapter import transcribe_audio

    with pytest.raises(ProviderUnavailableError):
        transcribe_audio(b"fake-audio")


def test_reason_about_text_raises_when_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from app.services.providers.openai_adapter import reason_about_text

    with pytest.raises(ProviderUnavailableError):
        reason_about_text("hello")


# ─── openai_adapter.py — happy path (mocked client) ──────────────────────────


def test_transcribe_audio_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")

    mock_response = MagicMock()
    mock_response.text = "This is the transcript."

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = mock_response

    with patch("app.services.providers.openai_adapter.get_openai_client", return_value=mock_client):
        from app.services.providers.openai_adapter import transcribe_audio

        result = transcribe_audio(b"audio-bytes", filename="test.mp3")

    assert result["transcript"] == "This is the transcript."
    assert result["provenance"]["provider"] == "openai"
    assert result["provenance"]["model"] == "whisper-1"
    mock_client.audio.transcriptions.create.assert_called_once()


def test_reason_about_text_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")

    payload = {"summary": "A short summary.", "tags": ["work", "meeting"], "project_task": "Q2 Review"}
    mock_message = MagicMock()
    mock_message.content = json.dumps(payload)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("app.services.providers.openai_adapter.get_openai_client", return_value=mock_client):
        from app.services.providers.openai_adapter import reason_about_text

        result = reason_about_text("Meeting notes about Q2.")

    assert result["enriched_content"] == "A short summary."
    assert result["tags"] == ["work", "meeting"]
    assert result["inferred_project_task"] == "Q2 Review"
    assert result["provenance"]["provider"] == "openai"
    assert result["provenance"]["model"] == "gpt-4o"


def test_reason_about_text_handles_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")

    mock_message = MagicMock()
    mock_message.content = "not valid json at all"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("app.services.providers.openai_adapter.get_openai_client", return_value=mock_client):
        from app.services.providers.openai_adapter import reason_about_text

        result = reason_about_text("some text")

    # Falls back gracefully — enriched_content set to the raw model output
    assert "enriched_content" in result
    assert result["tags"] == []
    assert result["inferred_project_task"] is None


# ─── gemini_adapter.py — fallback (no key) ────────────────────────────────────


def test_analyse_screenshot_raises_when_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from app.services.providers.gemini_adapter import analyse_screenshot

    with pytest.raises(ProviderUnavailableError):
        analyse_screenshot(b"fake-image")


# ─── gemini_adapter.py — happy path (mocked client) ──────────────────────────


def test_analyse_screenshot_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-fake")

    vision_payload = {
        "description": "A terminal session showing Python code.",
        "tags": ["coding", "python"],
        "ocr_text": "def hello(): pass",
        "project_task": "Lookback dev",
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(vision_payload)

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model

    with patch("app.services.providers.gemini_adapter.get_gemini_client", return_value=mock_genai):
        from app.services.providers.gemini_adapter import analyse_screenshot

        result = analyse_screenshot(b"image-bytes", mime_type="image/png")

    assert result["description"] == "A terminal session showing Python code."
    assert result["tags"] == ["coding", "python"]
    assert result["ocr_text"] == "def hello(): pass"
    assert result["inferred_project_task"] == "Lookback dev"
    assert result["provenance"]["provider"] == "gemini"
    assert result["provenance"]["model"] == "gemini-2.0-flash"


def test_analyse_screenshot_strips_markdown_fences(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-fake")

    raw_json = {"description": "A chart.", "tags": [], "ocr_text": "", "project_task": None}
    fenced = f"```json\n{json.dumps(raw_json)}\n```"

    mock_response = MagicMock()
    mock_response.text = fenced

    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response

    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model

    with patch("app.services.providers.gemini_adapter.get_gemini_client", return_value=mock_genai):
        from app.services.providers.gemini_adapter import analyse_screenshot

        result = analyse_screenshot(b"image-bytes")

    assert result["description"] == "A chart."
    assert result["inferred_project_task"] is None


# ─── ingestion pipeline — ingest_audio fallback ───────────────────────────────


def test_ingest_audio_falls_back_when_provider_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    payload = ingest_audio(b"fake-audio")

    assert payload["source_type"] == "audio"
    assert "unavailable" in payload["raw_content"].lower()
    assert payload["provenance"]["provider"] == "fallback"


def test_ingest_audio_uses_transcript_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")

    mock_result = {
        "transcript": "Hello world from Whisper.",
        "provenance": {"provider": "openai", "model": "whisper-1"},
    }

    with patch(
        "app.services.providers.openai_adapter.transcribe_audio", return_value=mock_result
    ) as mock_transcribe:
        payload = ingest_audio(b"real-audio", filename="clip.mp3")

    mock_transcribe.assert_called_once_with(b"real-audio", filename="clip.mp3")
    assert payload["raw_content"] == "Hello world from Whisper."
    assert payload["source_type"] == "audio"
    assert payload["provenance"]["provider"] == "openai"


# ─── enrichment pipeline — fallback paths ────────────────────────────────────


def test_enrich_with_context_falls_back_when_provider_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = enrich_with_context("some raw text")

    assert "enriched_content" in result
    assert "enriched_provenance" in result
    assert result["enriched_provenance"]["provider"] == "internal"


def test_enrich_with_screenshot_falls_back_when_provider_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = enrich_with_screenshot(b"fake-image")

    assert "enriched_content" in result
    assert result["enriched_provenance"]["provider"] == "fallback"
    assert result["tags"] == []
    assert result["ocr_text"] == ""
