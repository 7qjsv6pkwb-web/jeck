.PHONY: db-up db-down migrate test test-int api

SHELL := /bin/bash

db-up:
	docker compose up -d db

db-down:
	docker compose down

migrate:
	cd backend && poetry run alembic upgrade head

test:
	cd backend && poetry run pytest -q

test-int:
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "DATABASE_URL is required for integration tests" >&2; \
		exit 1; \
	fi
	cd backend && poetry run alembic upgrade head
	cd backend && poetry run pytest -q -m integration

api:
	cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
