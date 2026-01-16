.PHONY: db-up db-down migrate test test-int api

SHELL := /bin/bash

db-up:
	docker compose up -d db

db-down:
	docker compose down

migrate:
	cd backend && poetry run alembic upgrade head

test:
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "Poetry is required. Install it and re-run: https://python-poetry.org/docs/#installation" >&2; \
		exit 1; \
	fi
	cd backend && poetry run pytest -q

test-int:
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "DATABASE_URL is required for integration tests" >&2; \
		exit 1; \
	fi
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "Poetry is required. Install it and re-run: https://python-poetry.org/docs/#installation" >&2; \
		exit 1; \
	fi
	@cd backend && poetry run python - <<'PY'
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

engine = create_engine("${DATABASE_URL}")
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except SQLAlchemyError as exc:
    raise SystemExit(f"Database connection failed: {exc}") from exc
PY
	cd backend && poetry run alembic upgrade head
	cd backend && poetry run pytest -q -m integration

api:
	cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
