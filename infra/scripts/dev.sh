#!/usr/bin/env bash
set -euo pipefail

(
  cd backend
  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

(
  cd frontend
  npm run dev
) &
FRONTEND_PID=$!

# cleanup terminates the backend and frontend background processes and suppresses any errors or output.
cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM
wait
