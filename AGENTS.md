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

## Docs policy (AGENTS vs README)
- **AGENTS.md** — single source of truth for project rules: guardrails, conventions, agent/Codex behavior, PR/commit requirements, testing/migrations policies.
- **README.md** — only “how to run/use”: quick start, dependencies, env vars, commands, links.
- If a note changes how we *work* (process/rules) → **AGENTS.md**. If it changes how we *run* (usage) → **README.md**.

## Setup & commands (Poetry)
- Install deps: `cd backend && poetry install`
- Run tests: `cd backend && poetry run pytest -q`
- Start DB: `docker compose up -d db`
- Run migrations: `cd backend && poetry run alembic upgrade head`

## Code conventions
- Use a service layer for action state machine (no business logic in routers).
- Validate inputs/outputs with Pydantic schemas.
- Add idempotency_key to actions and keep approve idempotent.

## Collaboration model (Owner / Tech Lead / Codex)

### Roles
- **Product/Owner (human)**:
  - Sets high-level goals, priorities, acceptance criteria in user terms.
  - Accepts/rejects changes (“like/dislike”), decides what gets merged to `main`.
- **Head / Tech Lead (this assistant)**:
  - Translates goals into precise engineering tasks for Codex.
  - Defines scope, files to change, constraints, DoD, tests, PR format.
- **Codex (executor)**:
  - Works only via Git changes (branch → commits → checks → PR).
  - Does NOT invent architecture; follows repo conventions + this AGENTS.md.

---

## Codex working rules (must follow)

### Always sync & inspect first
Before any change, Codex MUST:
1. `git fetch --all --prune`
2. `git checkout main && git pull --ff-only`
3. `cd backend && ls -la && find app -maxdepth 3 -type f | head`
4. Search in codebase for relevant symbols/routes/tests:
   - `rg -n "<keyword>" backend/app || true`

Codex must not re-implement already-existing files/logic. If something exists, extend it.

### One task = one PR = small diff
- Keep PR scope minimal (ideally **< 200 LOC changed** unless unavoidable).
- No “drive-by refactors”.
- No unrelated formatting.
- If multiple steps are needed, split into PR-1, PR-2, etc.

### Patch / apply hygiene
- Never paste shell snippets into `.py` files.
- Never output broken here-docs; ensure EOF on its own line.
- Prefer editing files directly in repo rather than generating patch blocks that frequently corrupt.

### Definition of Done (DoD) for every PR
A PR is “Done” only if:
1. **All tests green**:
   - `cd backend && poetry run pytest -q`
   - `cd backend && poetry run pytest -q -m integration` (if DATABASE_URL available)
2. **Imports work** (no missing modules / circular imports).
3. **No dead code paths** in routers (404 routes referenced by tests must exist).
4. **New functionality has tests** (unit or integration; minimal but real).
5. **Updated docs** only if behavior/commands changed (README stays launch-only; rules live here).

### Required local checks (Codex must run and paste output in PR summary)
From repo root:
- `cd backend && poetry install` (only if deps changed)
- `cd backend && poetry run pytest -q`
- `cd backend && poetry run pytest -q -m integration` (if env+DB are available)
- If API routes changed: show 2 curls (example):
  - `curl -i http://localhost:8000/health`
  - `curl -i http://localhost:8000/v1/<resource>?limit=5`

### PR summary format (mandatory)
Each PR description must contain:
- **What**: 2–5 bullets of changes
- **Why**: 1–2 bullets referencing goal/bug
- **How to test**: exact commands + expected outputs
- **Files changed**: short list
- **Notes / risks**: migrations, breaking changes, env vars, etc.

---

## Project conventions
- Routers are thin: they call `app/services/*` (business logic lives in services).
- Pydantic schemas in `app/schemas/*` must be importable without side effects.
- Guardrails:
  - Approve is **web-only**.
  - EXECUTE forbidden unless `status == APPROVED`.
  - All approve + execution outcomes must go to audit log.

---

## Standard dev commands (source of truth)
From repo root:
- Start DB: `docker compose up -d db`
- Backend (tests): `cd backend && poetry run pytest -q`
- Backend (integration): `cd backend && poetry run pytest -q -m integration`
- Migrations: `cd backend && poetry run alembic upgrade head`
- Run API: `cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`