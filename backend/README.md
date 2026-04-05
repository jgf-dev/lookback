# Lookback Backend (FastAPI)

## Run

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Core endpoints

- `POST /audio/transcribe`: transcribe voice comments
- `POST /entries`: store typed/thought entries + deep enrichment
- `POST /screenshots`: analyze screenshot + save timeline entry
- `GET /timeline`: rolling day timeline
- `POST /insights/generate`: trend and action suggestions
- `POST /day/finish`: generate end-of-day summary for voice review session
