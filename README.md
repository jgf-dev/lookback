# lookback

Monorepo scaffold for a split backend/frontend application with shared contracts and CI automation.

## Top-level layout

- `backend/` – Python FastAPI service.
- `frontend/` – Next.js web app.
- `shared/` – Contracts as Pydantic, TypeScript, and JSON Schema.
- `infra/` – Dev scripts and docker compose config.
- `.github/workflows/` – CI for lint and tests.
- `docs/` – Architecture and design notes.

## Architecture overview

See `docs/architecture.md` for full detail. High-level flow:

1. Ingestion (backend receives input)
2. Enrichment (normalize/validate against shared contracts)
3. Analysis (compute response)
4. Storage (future pluggable persistence)
5. Presentation (frontend UI and API display)

## Local development

### Prerequisites

- Python 3.10+
- Node.js 22+
- npm 10+

### Setup

```bash
make setup
```

### Run independently

Backend only:

```bash
make backend-dev
```

Frontend only:

```bash
make frontend-dev
```

### Run together

```bash
make dev
```

Alternative with Docker Compose:

```bash
docker compose -f infra/docker-compose.dev.yml up
```

## Environment variables

### Backend

- `PORT` (optional): backend port; default `8000`.

### Frontend

- `NEXT_PUBLIC_BACKEND_URL`: backend base URL for browser calls.
  - Default: `http://localhost:8000`

## Security notes

- Keep `.env` and secrets out of git (enforced by `.gitignore`).
- Use least-privilege credentials for future storage/third-party APIs.
- Validate and sanitize all external inputs through shared contracts.
- Add authentication and authorization before exposing non-public endpoints.

## Quality checks

```bash
make lint
make test
```

CI runs linting and tests on every push/PR.