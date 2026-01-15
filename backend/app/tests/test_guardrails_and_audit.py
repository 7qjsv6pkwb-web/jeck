import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import get_db_session
from app.main import app


BASE_DIR = Path(__file__).resolve().parents[2]


def run_migrations(database_url: str) -> None:
    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")


def _mk_client(database_url: str) -> TestClient:
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db_session():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = override_db_session
    return TestClient(app)


def _create_project_thread(client: TestClient):
    project = client.post("/v1/projects", json={"slug": "demo", "name": "Demo", "settings": {}}).json()
    thread = client.post(f"/v1/projects/{project['id']}/threads", json={"title": "Hello", "tags": {}}).json()
    return project, thread


@pytest.mark.integration
def test_execute_requires_approved_and_execute_policy(monkeypatch):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for integration tests")

    monkeypatch.setenv("DATABASE_URL", database_url)
    run_migrations(database_url)

    client = _mk_client(database_url)
    _project, thread = _create_project_thread(client)

    # policy_mode=DRAFT should block execute even if approved
    a1 = client.post(
        f"/v1/threads/{thread['id']}/actions",
        json={"type": "stub.echo", "policy_mode": "DRAFT", "payload": {"x": 1}, "idempotency_key": "idem-gr-1"},
    ).json()

    client.post(f"/v1/actions/{a1['id']}/approve", json={"approved_by": "tester", "channel": "web"}).raise_for_status()
    r = client.post(f"/v1/actions/{a1['id']}/execute")
    assert r.status_code == 409

    # policy_mode=EXECUTE but not approved should block execute
    a2 = client.post(
        f"/v1/threads/{thread['id']}/actions",
        json={"type": "stub.echo", "policy_mode": "EXECUTE", "payload": {"x": 2}, "idempotency_key": "idem-gr-2"},
    ).json()
    r2 = client.post(f"/v1/actions/{a2['id']}/execute")
    assert r2.status_code == 409


@pytest.mark.integration
def test_approve_web_only_and_audit_events_written(monkeypatch):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for integration tests")

    monkeypatch.setenv("DATABASE_URL", database_url)
    run_migrations(database_url)

    client = _mk_client(database_url)
    project, thread = _create_project_thread(client)

    action = client.post(
        f"/v1/threads/{thread['id']}/actions",
        json={"type": "stub.echo", "policy_mode": "EXECUTE", "payload": {"x": 7}, "idempotency_key": "idem-gr-3"},
    ).json()

    # telegram approve must be rejected
    bad = client.post(f"/v1/actions/{action['id']}/approve", json={"approved_by": "tester", "channel": "telegram"})
    assert bad.status_code == 409

    # web approve OK + execute OK
    ok = client.post(f"/v1/actions/{action['id']}/approve", json={"approved_by": "tester", "channel": "web"})
    ok.raise_for_status()

    ex = client.post(f"/v1/actions/{action['id']}/execute")
    ex.raise_for_status()
    assert ex.json()["status"] in ("DONE", "FAILED")

    # audit must have entries for this action
    audit = client.get(f"/v1/audit?project_id={project['id']}&action_id={action['id']}&limit=50")
    audit.raise_for_status()
    rows = audit.json()
    assert len(rows) >= 2, "Expected at least created+approved (and usually executing/done) audit events"
