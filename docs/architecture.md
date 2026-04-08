# Architecture

## System layers

### 1. Ingestion layer

- Implemented by backend HTTP endpoints (`/health`, `/analyze`).
- Responsible for request acceptance and initial parsing.

### 2. Enrichment layer

- Shared contracts in `shared/` define canonical request/response shape.
- Backend validates with Pydantic models.
- Frontend uses matching TypeScript interfaces.

### 3. Analysis layer

- Backend contains domain logic in service handlers.
- Current scaffold computes a basic summary and confidence score.
- Designed so analysis can be swapped for an LLM/ML pipeline later.

### 4. Storage layer

- Not yet implemented; intended insertion point for database and object store.
- Recommended pattern:
  - repository interfaces in backend
  - migration scripts in `infra/` or backend subfolder

### 5. Presentation layer

- Next.js frontend renders UI and references backend endpoints.
- Environment-driven backend URL allows local/staging/prod switching.

## Dev operation model

- Independent mode:
  - Backend and frontend are startable with separate commands.
- Unified mode:
  - `make dev` starts both processes via `infra/scripts/dev.sh`.
  - Docker compose option is provided for containerized local runs.

## CI automation

- GitHub Actions workflow runs lint + test for backend and frontend.
- Unit tests cover backend API behavior and frontend URL utility logic.
