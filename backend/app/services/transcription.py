from __future__ import annotations

import asyncio
import audioop
import os
import random
import time
import wave
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


@dataclass
class TranscriptSegment:
    text: str
    start_ts_ms: int
    end_ts_ms: int
    speaker: str
    confidence: float
    session_id: str
    day_id: str
    provisional: bool = False


class TranscriptStore:
    """Simple persistence layer backed by an append-only JSONL file."""

    def __init__(self, output_path: str | None = None) -> None:
        self._segments: list[TranscriptSegment] = []
        default_path = Path("backend/data/transcripts.jsonl")
        self._output_path = Path(output_path) if output_path else default_path
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, segment: TranscriptSegment) -> None:
        import json

        self._segments.append(segment)
        with self._output_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(segment), ensure_ascii=False) + "\n")

    def list_for_session(self, session_id: str) -> list[TranscriptSegment]:
        return [s for s in self._segments if s.session_id == session_id]


class TranscriptionService:
    """Buffers PCM16 chunks, detects activity/silence segments, and transcribes segments."""

    def __init__(
        self,
        sample_rate_hz: int = 16_000,
        bytes_per_sample: int = 2,
        silence_threshold_rms: int = 550,
        min_speech_ms: int = 300,
        silence_hold_ms: int = 700,
        speaker_default: str = "user",
        openai_model: str = "gpt-4o-mini-transcribe",
        gemini_model: str = "gemini-2.5-flash",
        store: TranscriptStore | None = None,
    ) -> None:
        self.sample_rate_hz = sample_rate_hz
        self.bytes_per_sample = bytes_per_sample
        self.silence_threshold_rms = silence_threshold_rms
        self.min_speech_ms = min_speech_ms
        self.silence_hold_ms = silence_hold_ms
        self.speaker_default = speaker_default
        self.openai_model = openai_model
        self.gemini_model = gemini_model
        self.store = store or TranscriptStore()

        self._segment_buffer = bytearray()
        self._in_speech = False
        self._speech_start_ms = 0
        self._last_activity_ms = 0
        self._stream_started_monotonic = time.monotonic()

    def reset_stream(self) -> None:
        self._segment_buffer.clear()
        self._in_speech = False
        self._speech_start_ms = 0
        self._last_activity_ms = 0
        self._stream_started_monotonic = time.monotonic()

    def _elapsed_ms(self) -> int:
        return int((time.monotonic() - self._stream_started_monotonic) * 1000)

    async def ingest_chunk(
        self,
        chunk: bytes,
        session_id: str,
        day_id: str | None = None,
    ) -> tuple[list[TranscriptSegment], dict[str, Any]]:
        """
        Ingests one PCM16 chunk and returns finalized segments (if any) + health payload.
        """
        now_ms = self._elapsed_ms()
        day = day_id or date.today().isoformat()

        rms = audioop.rms(chunk, self.bytes_per_sample) if chunk else 0
        is_active = rms >= self.silence_threshold_rms

        if is_active:
            if not self._in_speech:
                self._in_speech = True
                self._speech_start_ms = now_ms
            self._last_activity_ms = now_ms
            self._segment_buffer.extend(chunk)
        elif self._in_speech:
            self._segment_buffer.extend(chunk)
            silence_ms = now_ms - self._last_activity_ms
            if silence_ms >= self.silence_hold_ms:
                segment_duration = now_ms - self._speech_start_ms
                if segment_duration >= self.min_speech_ms:
                    finalized = await self._finalize_segment(
                        bytes(self._segment_buffer),
                        self._speech_start_ms,
                        now_ms,
                        session_id,
                        day,
                    )
                    self._segment_buffer.clear()
                    self._in_speech = False
                    return [finalized], {
                        "type": "health",
                        "status": "ok",
                        "rms": rms,
                        "active": is_active,
                        "retryCount": 0,
                    }

                # too short, drop as noise
                self._segment_buffer.clear()
                self._in_speech = False

        # keep short provisional previews for UI continuity
        provisional: list[TranscriptSegment] = []
        if self._in_speech and len(self._segment_buffer) > self.sample_rate_hz * self.bytes_per_sample:
            preview = TranscriptSegment(
                text="Listening…",
                start_ts_ms=self._speech_start_ms,
                end_ts_ms=now_ms,
                speaker=self.speaker_default,
                confidence=0.0,
                session_id=session_id,
                day_id=day,
                provisional=True,
            )
            provisional.append(preview)

        return provisional, {
            "type": "health",
            "status": "ok",
            "rms": rms,
            "active": is_active,
            "retryCount": 0,
        }

    async def flush(self, session_id: str, day_id: str | None = None) -> list[TranscriptSegment]:
        if not self._in_speech or not self._segment_buffer:
            return []
        now_ms = self._elapsed_ms()
        day = day_id or date.today().isoformat()
        segment_duration = now_ms - self._speech_start_ms
        if segment_duration < self.min_speech_ms:
            self._segment_buffer.clear()
            self._in_speech = False
            return []

        finalized = await self._finalize_segment(
            bytes(self._segment_buffer),
            self._speech_start_ms,
            now_ms,
            session_id,
            day,
        )
        self._segment_buffer.clear()
        self._in_speech = False
        return [finalized]

    async def _finalize_segment(
        self,
        pcm16_audio: bytes,
        start_ts_ms: int,
        end_ts_ms: int,
        session_id: str,
        day_id: str,
    ) -> TranscriptSegment:
        text, confidence, retries = await self._transcribe_with_retry(pcm16_audio)
        if not text:
            text = "[Unrecognized speech]"

        segment = TranscriptSegment(
            text=text,
            start_ts_ms=start_ts_ms,
            end_ts_ms=end_ts_ms,
            speaker=self.speaker_default,
            confidence=confidence,
            session_id=session_id,
            day_id=day_id,
            provisional=False,
        )
        self.store.add(segment)
        return segment

    async def _transcribe_with_retry(self, pcm16_audio: bytes) -> tuple[str, float, int]:
        max_attempts = 4
        base_delay = 0.4
        last_error: Exception | None = None

        for attempt in range(max_attempts):
            try:
                text, confidence = await self._transcribe_openai(pcm16_audio)
                return text, confidence, attempt
            except Exception as openai_err:
                last_error = openai_err
                try:
                    text, confidence = await self._transcribe_gemini(pcm16_audio)
                    return text, confidence, attempt
                except Exception as gemini_err:
                    last_error = gemini_err

            delay = base_delay * (2**attempt) + random.uniform(0, 0.2)
            await asyncio.sleep(delay)

        if last_error:
            return f"[Transcription failed: {last_error}]", 0.0, max_attempts
        return "", 0.0, max_attempts

    async def _transcribe_openai(self, pcm16_audio: bytes) -> tuple[str, float]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed") from exc

        with NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            self._write_wav(tmp.name, pcm16_audio)
            client = AsyncOpenAI(api_key=api_key)
            with open(tmp.name, "rb") as f:
                resp = await client.audio.transcriptions.create(
                    model=self.openai_model,
                    file=f,
                )
        text = getattr(resp, "text", "")
        confidence = float(getattr(resp, "confidence", 0.92))
        return text.strip(), confidence

    async def _transcribe_gemini(self, pcm16_audio: bytes) -> tuple[str, float]:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError("google-generativeai package is not installed") from exc

        with NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            self._write_wav(tmp.name, pcm16_audio)
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.gemini_model)
            uploaded = genai.upload_file(path=tmp.name)
            resp = await asyncio.to_thread(
                model.generate_content,
                [
                    "Transcribe this audio. Return only transcript text.",
                    uploaded,
                ],
            )
            text = (resp.text or "").strip()
            return text, 0.78

    def _write_wav(self, path: str, pcm16_audio: bytes) -> None:
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.bytes_per_sample)
            wf.setframerate(self.sample_rate_hz)
            wf.writeframes(pcm16_audio)
