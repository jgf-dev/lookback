# Deployment notes

1. Copy `.env.example` to `.env` in both `backend/` and `frontend/` and set secrets.
2. Build and run services from `infra/`:

```bash
docker compose up --build
```

3. Add object storage and production database before first external deployment.
