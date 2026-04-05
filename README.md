# lookback

## Backend setup (`backend/`)

### 1) Install dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment

Create `backend/.env`:

```env
DATABASE_URL=sqlite:///./lookback.db
OPENAI_API_KEY=
GEMINI_API_KEY=
```

For PostgreSQL, set e.g. `DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/lookback`.

### 3) Run migrations

```bash
cd backend
alembic upgrade head
```

### 4) Start API

```bash
cd backend
uvicorn app.main:app --reload
```

Key routes:
- `GET /entries`
- `GET /entries/search?query=...`
- `POST /entries/deep-search`
- `POST /entries`
- `WS /ws/audio`
