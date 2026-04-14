from datetime import datetime, timezone

from app.services.providers.config import ProviderUnavailableError


def build_ingest_payload(source_type: str, raw_content: str) -> dict:
    return {
        "source_type": source_type,
        "raw_content": raw_content,
        "timestamp": datetime.now(timezone.utc),
    }


def ingest_speech(text: str) -> dict:
    return build_ingest_payload(source_type="speech", raw_content=text)


def ingest_screenshot(ocr_text: str) -> dict:
    return build_ingest_payload(source_type="screenshot", raw_content=ocr_text)


def ingest_manual_note(note: str) -> dict:
    return build_ingest_payload(source_type="manual_note", raw_content=note)


def ingest_audio(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """Transcribe *audio_bytes* via OpenAI Whisper and return an ingest payload.

    Falls back to a placeholder transcript when the provider is unavailable
    (SDK not installed or ``OPENAI_API_KEY`` not set).

    Args:
        audio_bytes: Raw audio file bytes (webm, mp4, mp3, wav, …).
        filename:    Original filename; used as a MIME hint by the Whisper API.

    Returns:
        Ingest payload dict with ``source_type="audio"``, ``raw_content`` set to
        the transcript (or placeholder), and a ``provenance`` key describing the
        transcription source.
    """
    try:
        from app.services.providers.openai_adapter import transcribe_audio  # noqa: PLC0415

        result = transcribe_audio(audio_bytes, filename=filename)
        transcript = result["transcript"]
        provenance = result["provenance"]
    except ProviderUnavailableError:
        transcript = "[transcription unavailable — OpenAI provider not configured]"
        provenance = {"provider": "fallback", "method": "placeholder"}

    payload = build_ingest_payload(source_type="audio", raw_content=transcript)
    payload["provenance"] = provenance
    return payload
