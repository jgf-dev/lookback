from __future__ import annotations

import base64

from app.config import get_settings


class TranscriptionService:
    """Best-effort STT integration for OpenAI or Gemini based on configured keys."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def transcribe_chunk(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
        if self.settings.openai_api_key:
            return self._transcribe_openai(audio_bytes)
        if self.settings.gemini_api_key:
            return self._transcribe_gemini(audio_bytes, mime_type)

        # Local-dev fallback to keep websocket flow alive.
        size = len(audio_bytes)
        return f"[transcription unavailable: received {size} bytes]"

    def _transcribe_openai(self, audio_bytes: bytes) -> str:
        from io import BytesIO

        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)
        file_obj = BytesIO(audio_bytes)
        file_obj.name = "chunk.webm"
        response = client.audio.transcriptions.create(model="gpt-4o-mini-transcribe", file=file_obj)
        return response.text

    def _transcribe_gemini(self, audio_bytes: bytes, mime_type: str) -> str:
        import google.generativeai as genai

        genai.configure(api_key=self.settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        encoded = base64.b64encode(audio_bytes).decode("utf-8")
        response = model.generate_content(
            [
                "Transcribe this audio and return only plain text.",
                {
                    "mime_type": mime_type,
                    "data": encoded,
                },
            ]
        )
        return response.text.strip()
