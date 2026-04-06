from __future__ import annotations

import asyncio
from datetime import datetime

from fastapi import Depends, FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.config import get_settings
from app.db.models import DailySummary, Entry, Insight
from app.db.session import get_session, init_db
from app.schemas import EntryIn, EntryOut, InsightOut, ScreenshotIn
from app.services.ai_clients import ai_clients
from app.services.insights import generate_insights, safe_metadata

app = FastAPI(title='Lookback API', version='0.1.0')

allowed_origins = get_settings().allowed_origins.split(',') if get_settings().allowed_origins != '*' else ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['*'],
)


@app.on_event('startup')
def on_startup() -> None:
    """
    Initialize and prepare the application's database on startup.
    
    This runs database initialization routines (e.g., creating tables and applying initial setup) when the application starts.
    """
    init_db()


@app.get('/health')
def health() -> dict[str, str]:
    """
    Return a simple health status for the API.
    
    Returns:
        dict[str, str]: A dictionary with the key 'status' set to 'ok' indicating the service is healthy.
    """
    return {'status': 'ok'}


@app.post('/entries', response_model=EntryOut)
def add_entry(payload: EntryIn, session: Session = Depends(get_session)) -> Entry:
    """
    Create and persist a new Entry from the provided payload, enriching its content before storage.
    
    Parameters:
        payload: Input data for the entry; its `content` is enriched and the original `metadata` is stored under `metadata_json` alongside the enrichment.
    
    Returns:
        The persisted Entry with database-populated fields (for example `id` and `created_at`) populated.
    """
    enrichment = ai_clients.deep_search(payload.content)
    entry = Entry(
        source=payload.source,
        content=payload.content,
        project=payload.project,
        task=payload.task,
        context=payload.context,
        metadata_json=safe_metadata({'user_metadata': payload.metadata, 'enrichment': enrichment}),
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.post('/audio/transcribe', response_model=EntryOut)
async def transcribe_audio(
    audio: UploadFile,
    project: str | None = None,
    task: str | None = None,
    context: str | None = None,
    session: Session = Depends(get_session),
) -> Entry:
    """
    Transcribe an uploaded audio file and store the result as a voice entry.
    
    Parameters:
        audio (UploadFile): Uploaded audio file to be transcribed.
        project (str | None): Optional project identifier to attach to the entry.
        task (str | None): Optional task identifier to attach to the entry.
        context (str | None): Optional contextual string to attach to the entry.
    
    Returns:
        entry (Entry): The persisted Entry with source set to 'voice' and content set to the transcription text.
    """
    audio_bytes = await audio.read()
    text = await asyncio.to_thread(ai_clients.transcribe_audio, audio_bytes)
    entry = Entry(source='voice', content=text, project=project, task=task, context=context)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.post('/screenshots', response_model=EntryOut)
def add_screenshot(payload: ScreenshotIn, session: Session = Depends(get_session)) -> Entry:
    """
    Create and persist an Entry representing an analyzed screenshot.
    
    Analyzes the provided base64 image (using the payload's context when present), constructs an Entry with source 'screenshot', stores capture metadata (captured_at), saves the Entry to the database, and returns the persisted record.
    
    Parameters:
        payload (ScreenshotIn): Input containing `image_b64`, optional `context`, `project`, and `task`.
    
    Returns:
        entry (Entry): The persisted Entry record for the analyzed screenshot.
    """
    analysis = ai_clients.analyze_screenshot(payload.image_b64, payload.context or '')
    entry = Entry(
        source='screenshot',
        content=analysis,
        project=payload.project,
        task=payload.task,
        context=payload.context,
        metadata_json=safe_metadata({'captured_at': datetime.utcnow().isoformat()}),
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.get('/timeline', response_model=list[EntryOut])
def get_timeline(session: Session = Depends(get_session)) -> list[Entry]:
    """
    Retrieve all stored entries ordered by creation time (oldest first).
    
    Returns:
        list[Entry]: Entries ordered by Entry.created_at in ascending order.
    """
    return session.exec(select(Entry).order_by(Entry.created_at)).all()


@app.post('/insights/generate', response_model=list[InsightOut])
def run_insights(session: Session = Depends(get_session)) -> list[Insight]:
    """
    Generate insights from stored entries and persist them to the database.
    
    Returns:
        list[Insight]: Insight records created or updated by the generation process.
    """
    return generate_insights(session)


@app.get('/insights', response_model=list[InsightOut])
def list_insights(session: Session = Depends(get_session)) -> list[Insight]:
    """
    Return all insights ordered by creation time, newest first.
    
    Returns:
        list[Insight]: Insights ordered by descending creation timestamp (newest first).
    """
    return session.exec(select(Insight).order_by(Insight.created_at.desc())).all()


@app.post('/day/finish')
def finish_day(session: Session = Depends(get_session)) -> dict[str, str]:
    """
    Create or update today's end-of-day markdown summary from recent entries and persist it.

    Builds a markdown summary for the current UTC date containing up to the last 25 entries (each formatted as "- [source] first 160 characters of content"), stores or updates the DailySummary record for that date, commits the change, and returns a status indicator.

    Returns:
        dict[str, str]: {'status': 'summary_ready'} when the summary has been persisted.
    """
    now = datetime.utcnow()
    today = now.date()
    today_start = datetime(today.year, today.month, today.day, 0, 0, 0)
    today_end = datetime(today.year, today.month, today.day, 23, 59, 59, 999999)

    entries = session.exec(
        select(Entry)
        .where(Entry.created_at >= today_start, Entry.created_at <= today_end)
        .order_by(Entry.created_at)
    ).all()
    bullets = '\n'.join([f'- [{e.source}] {e.content[:160]}' for e in entries[-25:]])
    summary = f'# End-of-day review ({today})\n\n{bullets}\n\nNext step: launch real-time voice session to validate and correct.'

    try:
        session.add(DailySummary(date=today, summary_markdown=summary))
        session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.exec(select(DailySummary).where(DailySummary.date == today)).first()
        if existing:
            existing.summary_markdown = summary
            session.add(existing)
            session.commit()
    return {'status': 'summary_ready'}