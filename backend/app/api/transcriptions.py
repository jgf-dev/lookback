from fastapi import APIRouter
from pydantic import BaseModel

from app.services.transcription_service import transcribe_voice_entry

router = APIRouter()


class VoiceEntryRequest(BaseModel):
    text: str


@router.post("/voice-entry")
def voice_entry(payload: VoiceEntryRequest) -> dict[str, str]:
    transcript = transcribe_voice_entry(payload.text)
    return {"transcript": transcript}
