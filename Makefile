.PHONY: db-up db-down migrate test test-int api

db-up:
	docker compose up -d db

db-down:
	docker compose down

migrate:
	cd backend && poetry run alembic upgrade head

test:
	cd backend && poetry run pytest -q

test-int:
	cd backend && DATABASE_URL=$$(grep '^DATABASE_URL=' ../.env | cut -d= -f2-) poetry run pytest -q -m integration

api:
	cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
