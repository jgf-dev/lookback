"""OpenAI provider adapter.

Provides two capabilities:
- ``transcribe_audio``: converts raw audio bytes to text via OpenAI Whisper.
- ``reason_about_text``: sends a text + system prompt to GPT-4o and returns a structured dict.

Both functions raise ``ProviderUnavailableError`` when the SDK or API key is absent.
"""

import io
import json

from app.services.providers.config import get_openai_client

_WHISPER_MODEL = "whisper-1"
_REASONING_MODEL = "gpt-4o"


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """Transcribe *audio_bytes* using OpenAI Whisper.

    Args:
        audio_bytes: Raw bytes of the audio file (webm, mp4, mp3, wav, etc.).
        filename:    Hint for the MIME type; defaults to ``audio.webm``.

    Returns:
        ``{"transcript": str, "provenance": {"provider": "openai", "model": "whisper-1"}}``

    Raises:
        ProviderUnavailableError: SDK missing or key absent.
    """
    client = get_openai_client()
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    response = client.audio.transcriptions.create(
        model=_WHISPER_MODEL,
        file=audio_file,
    )
    return {
        "transcript": response.text,
        "provenance": {"provider": "openai", "model": _WHISPER_MODEL},
    }


def reason_about_text(text: str, system_prompt: str | None = None) -> dict:
    """Ask GPT-4o to analyse *text* and return a structured enrichment.

    Args:
        text:          The raw text content to analyse.
        system_prompt: Optional instruction overriding the default enrichment prompt.

    Returns:
        ``{"enriched_content": str, "tags": list[str], "inferred_project_task": str | None,
           "provenance": {"provider": "openai", "model": "gpt-4o"}}``

    Raises:
        ProviderUnavailableError: SDK missing or key absent.
    """
    client = get_openai_client()

    default_system = (
        "You are a personal productivity assistant. "
        "Given a note or transcript, extract: "
        "(1) a concise one-sentence summary, "
        "(2) up to five relevant tags as a JSON array, "
        "(3) the most likely project/task name (or null). "
        "Respond ONLY with valid JSON matching: "
        '{"summary": "...", "tags": [...], "project_task": "..." | null}'
    )

    messages = [
        {"role": "system", "content": system_prompt or default_system},
        {"role": "user", "content": text},
    ]

    response = client.chat.completions.create(
        model=_REASONING_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
    )

    if response and response.choices and len(response.choices) > 0:
        raw = response.choices[0].message.content or "{}"
    else:
        raw = "{}"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"summary": raw, "tags": [], "project_task": None}

    return {
        "enriched_content": parsed.get("summary", text),
        "tags": parsed.get("tags", []),
        "inferred_project_task": parsed.get("project_task"),
        "provenance": {"provider": "openai", "model": _REASONING_MODEL},
    }
