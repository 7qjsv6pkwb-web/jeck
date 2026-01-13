# Jack — AI Helper (MVP)

Backend foundation for the “Jack” assistant.
MVP goal: FastAPI + PostgreSQL + SQLAlchemy 2.0 + Alembic + Pytest.

## Repo structure
- `backend/` — FastAPI application (Poetry-managed)
- `docker-compose.yml` — local PostgreSQL for development
- `AGENTS.md` — project rules (important)

## Quick start (local)
> Steps 2–6 will work after PR-1 (backend scaffold) is merged.
> 
### 1) Prerequisites
- Docker + Docker Compose
- Python 3.11+ (recommended)
- Poetry installed

### 2) Run PostgreSQL
bash

docker compose up -d db

### 3) Install backend dependencies
bash

cd backend
poetry install

### 4) Run DB migrations
bash

poetry run alembic upgrade head

### 5) Run tests
bash

poetry run pytest -q

### 6) Run API
bash

poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

#### Healthcheck:
	•	GET http://localhost:8000/health

#### Development notes
	•	Config is provided via environment variables (see .env.example).
	•	Database URL example:
postgresql+psycopg://jack:jack@localhost:5432/jack


#### Epic A status
	•	A0 Backend scaffold
	•	A1 Database schema + migrations
	•	A2 API CRUD
	•	A3 Actions state machine + guardrails
	•	A4 Audit logging
	•	A5 Artifact storage
	•	A6 Executor contract + stub
	•	A7 Tests




