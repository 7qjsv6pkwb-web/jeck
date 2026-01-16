.PHONY: db-up db-down migrate test test-int api lint format format-check typecheck check

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
	cd backend && poetry run alembic upgrade head
	cd backend && poetry run pytest -q -m integration

lint:
	cd backend && poetry run ruff check .

format:
	cd backend && poetry run ruff format .

format-check:
	cd backend && poetry run ruff format --check .

typecheck:
	cd backend && poetry run mypy app

check: test lint format-check typecheck

api:
	cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
