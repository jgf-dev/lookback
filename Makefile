.PHONY: setup lint test dev backend-dev frontend-dev

setup:
	python -m pip install -e ./backend[dev]
	cd frontend && npm install

lint:
	cd backend && python -m ruff check .
	cd frontend && npm run lint

test:
	cd backend && python -m pytest
	cd frontend && npm run test

backend-dev:
	cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev:
	cd frontend && npm run dev

dev:
	./infra/scripts/dev.sh
