from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.services.transcription import TranscriptionService

app = FastAPI(title="Lookback Backend")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/audio-stream")
async def ws_audio_stream(websocket: WebSocket) -> None:
    await websocket.accept()

    session_id = websocket.query_params.get("sessionId") or str(uuid.uuid4())
    day_id = websocket.query_params.get("dayId") or datetime.now(UTC).date().isoformat()

    svc = TranscriptionService()

    await websocket.send_json(
        {
            "type": "session",
            "sessionId": session_id,
            "dayId": day_id,
            "message": "audio stream connected",
        }
    )

    try:
        while True:
            msg = await websocket.receive()

            if msg.get("type") == "websocket.disconnect":
                break

            if text := msg.get("text"):
                payload = json.loads(text)
                if payload.get("type") == "flush":
                    flushed = await svc.flush(session_id=session_id, day_id=day_id)
                    for seg in flushed:
                        await websocket.send_json(
                            {
                                "type": "segment",
                                "provisional": False,
                                "segment": seg.__dict__,
                            }
                        )
                continue

            chunk = msg.get("bytes") or b""
            segments, health = await svc.ingest_chunk(
                chunk=chunk,
                session_id=session_id,
                day_id=day_id,
            )

            for seg in segments:
                await websocket.send_json(
                    {
                        "type": "segment",
                        "provisional": seg.provisional,
                        "segment": seg.__dict__,
                    }
                )

            await websocket.send_json(health)

    except WebSocketDisconnect:
        flushed = await svc.flush(session_id=session_id, day_id=day_id)
        for seg in flushed:
            await websocket.send_json(
                {
                    "type": "segment",
                    "provisional": False,
                    "segment": seg.__dict__,
                }
            )
