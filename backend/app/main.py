from __future__ import annotations

from datetime import datetime

from fastapi import Depends, FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.db.models import DailySummary, Entry, Insight
from app.db.session import get_session, init_db
from app.schemas import EntryIn, EntryOut, InsightOut, ScreenshotIn
from app.services.ai_clients import ai_clients
from app.services.insights import generate_insights, safe_metadata

app = FastAPI(title='Lookback API', version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def on_startup() -> None:
    init_db()


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.post('/entries', response_model=EntryOut)
def add_entry(payload: EntryIn, session: Session = Depends(get_session)) -> Entry:
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
    audio_bytes = await audio.read()
    text = ai_clients.transcribe_audio(audio_bytes)
    entry = Entry(source='voice', content=text, project=project, task=task, context=context)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@app.post('/screenshots', response_model=EntryOut)
def add_screenshot(payload: ScreenshotIn, session: Session = Depends(get_session)) -> Entry:
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
    return session.exec(select(Entry).order_by(Entry.created_at)).all()


@app.post('/insights/generate', response_model=list[InsightOut])
def run_insights(session: Session = Depends(get_session)) -> list[Insight]:
    return generate_insights(session)


@app.get('/insights', response_model=list[InsightOut])
def list_insights(session: Session = Depends(get_session)) -> list[Insight]:
    return session.exec(select(Insight).order_by(Insight.created_at.desc())).all()


@app.post('/day/finish')
def finish_day(session: Session = Depends(get_session)) -> dict[str, str]:
    today = datetime.utcnow().strftime('%Y-%m-%d')
    entries = session.exec(select(Entry).order_by(Entry.created_at)).all()
    bullets = '\n'.join([f'- [{e.source}] {e.content[:160]}' for e in entries[-25:]])
    summary = f'# End-of-day review ({today})\n\n{bullets}\n\nNext step: launch real-time voice session to validate and correct.'

    existing = session.exec(select(DailySummary).where(DailySummary.date == today)).first()
    if existing:
        existing.summary_markdown = summary
        session.add(existing)
    else:
        session.add(DailySummary(date=today, summary_markdown=summary))
    session.commit()
    return {'status': 'summary_ready'}
