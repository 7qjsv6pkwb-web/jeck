SHELL := /bin/bash

.PHONY: test test-integration up down migrate api

test:
	poetry run pytest -q

test-integration:
	poetry run pytest -q -m integration

up:
	docker compose up -d db

down:
	docker compose down

migrate:
	poetry run alembic upgrade head

api:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
