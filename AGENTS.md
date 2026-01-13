# AGENTS.md — Project rules for Jack (Epic A)

## Goal (Epic A)
Build backend foundation: FastAPI + Postgres + SQLAlchemy 2.0 + Alembic + Pytest.

## Non-negotiable safety/guardrails
- Policy modes: READ, DRAFT, EXECUTE.
- Action statuses: DRAFT, APPROVED, EXECUTING, DONE, FAILED, CANCELED.
- EXECUTE is forbidden unless action.status == APPROVED.
- Approve can be performed only by a web user (not Telegram/bot).
- Every approve and every execution outcome must be written to audit log.

## Repo structure (target)
- backend/app for application code
- backend/app/db for models/session/migrations
- backend/app/api for routes
- backend/app/services for business logic (actions/audit)
- backend/app/tests for pytest

## Setup & commands (Poetry)
- Install deps: `cd backend && poetry install`
- Run tests: `cd backend && poetry run pytest -q`
- Start DB: `docker compose up -d db`
- Run migrations: `cd backend && poetry run alembic upgrade head`

## Code conventions
- Use a service layer for action state machine (no business logic in routers).
- Validate inputs/outputs with Pydantic schemas.
- Add idempotency_key to actions and keep approve idempotent.
