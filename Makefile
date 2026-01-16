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
	@cd backend && poetry run python -c 'exec("import os\nfrom sqlalchemy import create_engine, text\nfrom sqlalchemy.exc import SQLAlchemyError\n\nurl = os.getenv(\"DATABASE_URL\")\nif not url:\n    raise SystemExit(\"DATABASE_URL is not set\")\n\nengine = create_engine(url)\ntry:\n    with engine.connect() as conn:\n        conn.execute(text(\"SELECT 1\"))\nexcept SQLAlchemyError as exc:\n    raise SystemExit(f\"Database connection failed: {exc}\")\n")'
	cd backend && poetry run alembic upgrade head
	cd backend && poetry run pytest -q -m integration

api:
	cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
