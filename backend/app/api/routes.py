from uuid import uuid4

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.audio.stream_manager import StreamManager
from app.db import get_db
from app.journal.repository import JournalRepository
from app.journal.schemas import EntryCreate, EntryRead
from app.transcription.service import TranscriptionService

router = APIRouter()
stream_manager = StreamManager()
transcriber = TranscriptionService()


@router.get("/entries", response_model=list[EntryRead])
def list_entries(
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return JournalRepository(db).list_entries(limit=limit, offset=offset)


@router.get("/entries/search", response_model=list[EntryRead])
def search_entries(query: str, limit: int = 50, db: Session = Depends(get_db)):
    return JournalRepository(db).search_entries(query=query, limit=limit)


@router.post("/entries/deep-search", response_model=list[EntryRead])
def deep_search_entries(vector: list[float], limit: int = 20, db: Session = Depends(get_db)):
    return JournalRepository(db).deep_search_entries(vector=vector, limit=limit)


@router.websocket("/ws/audio")
async def audio_stream(websocket: WebSocket):
    await websocket.accept()
    session_key = str(uuid4())
    stream_manager.start(session_key)

    try:
        while True:
            message = await websocket.receive()

            if "bytes" in message and message["bytes"] is not None:
                stream_manager.append_chunk(session_key, message["bytes"])
                await websocket.send_json({"type": "ack", "bytes": len(message["bytes"])})
                continue

            text_payload = message.get("text")
            if text_payload == "flush":
                audio_blob = stream_manager.consume(session_key)
                transcript = transcriber.transcribe_chunk(audio_blob)
                await websocket.send_json({"type": "transcript", "text": transcript})
            elif text_payload == "close":
                break
    except WebSocketDisconnect:
        pass
    finally:
        stream_manager.close(session_key)
        await websocket.close()


@router.post("/entries", response_model=EntryRead)
def create_entry(payload: EntryCreate, db: Session = Depends(get_db)):
    return JournalRepository(db).create_entry(payload)
