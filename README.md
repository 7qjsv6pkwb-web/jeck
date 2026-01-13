# Jack — AI Helper (MVP)

Backend foundation for the “Jack” assistant.
MVP goal: FastAPI + PostgreSQL + SQLAlchemy 2.0 + Alembic + Pytest.

## Repo structure
- `backend/` — FastAPI application (Poetry-managed)
- `docker-compose.yml` — local PostgreSQL for development
- `AGENTS.md` — project rules (important)

## Quick start (local)
### 1) Prerequisites
- Docker + Docker Compose
- Python 3.11+ (recommended)
- Poetry installed

### 2) Run PostgreSQL
```bash
docker compose up -d db
