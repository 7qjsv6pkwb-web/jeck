import os
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from alembic import command
from app.db.session import get_db_session
from app.main import app

BASE_DIR = Path(__file__).resolve().parents[2]


def run_migrations(database_url: str) -> None:
    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")


def _find_audit_get_path() -> str:
    # Ищем любой GET-route, где в пути есть "audit"
    for r in app.routes:
        methods = getattr(r, "methods", set()) or set()
        path = getattr(r, "path", "")
        if "GET" in methods and "audit" in path:
            return path
    raise AssertionError(
        "No GET audit endpoint found in app routes (expected path contains 'audit')."
    )


@pytest.mark.integration
def test_audit_api_returns_events_for_action(monkeypatch):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for audit API integration test")

    monkeypatch.setenv("DATABASE_URL", database_url)
    run_migrations(database_url)

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db_session():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = override_db_session
    client = TestClient(app)

    # 1) create project + thread
    pr = client.post(
        "/v1/projects",
        json={"slug": "demo", "name": "Demo", "settings": {"tier": "dev"}},
    )
    pr.raise_for_status()
    project = pr.json()

    tr = client.post(
        f"/v1/projects/{project['id']}/threads",
        json={"title": "Hello", "tags": {"topic": "intro"}},
    )
    tr.raise_for_status()
    thread = tr.json()

    # 2) create action
    ar = client.post(
        f"/v1/threads/{thread['id']}/actions",
        json={
            "type": "example",
            "policy_mode": "DRAFT",
            "payload": {"input": "value"},
            "idempotency_key": "idem-audit-1",
        },
    )
    ar.raise_for_status()
    action = ar.json()

    # 3) approve action (web)
    appr = client.post(
        f"/v1/actions/{action['id']}/approve",
        json={"approved_by": "tester", "channel": "web"},
    )
    appr.raise_for_status()

    # 4) call audit endpoint (path autodetect)
    audit_path = _find_audit_get_path()

    # пробуем сначала с фильтром по action_id (если поддерживается)
    resp = client.get(audit_path, params={"action_id": action["id"]})
    if resp.status_code == 422:
        # если фильтр не поддерживается — просто без params
        resp = client.get(audit_path)

    resp.raise_for_status()
    data = resp.json()

    # допускаем, что API может возвращать {"items": [...]} или просто [...]
    items = data.get("items", data) if isinstance(data, dict) else data
    assert isinstance(items, list), f"Unexpected audit response shape: {type(data)}"

    event_types = [row.get("event_type") for row in items if isinstance(row, dict)]
    assert "action.created" in event_types
    assert "action.approved" in event_types

    app.dependency_overrides.clear()
