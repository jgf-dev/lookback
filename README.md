# lookback

AI-assisted personal timeline canvas.

## Stack
- **Backend:** Python + FastAPI + SQLModel
- **Frontend:** Next.js (App Router)
- **AI:** OpenAI + Gemini APIs

## Features implemented
- Continuous entry ingestion architecture for voice/text/screenshot events
- Audio transcription endpoint (`/audio/transcribe`)
- Screenshot capture analysis endpoint (`/screenshots`)
- Deep enrichment of entries using Gemini/OpenAI (`/entries`)
- Rolling daily timeline (`/timeline`)
- Trend and action insight generation (`/insights/generate`)
- End-of-day summary trigger for real-time review (`/day/finish`)
- Placeholder Nano Banana integration hook for relationship visualizations

## Run locally

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Open `http://localhost:3000`.

## Notes
This is an MVP scaffold focused on core data flow and integration points. In production, add:
- secure auth + encrypted storage
- event bus/worker for continuous background ingestion
- local microphone/screenshot agent (desktop or browser extension)
- robust schema for projects/tasks/contexts and cross-entry linking
- WebRTC real-time voice review session + correction UI
