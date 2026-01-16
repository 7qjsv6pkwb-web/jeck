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


@pytest.fixture()
def client(monkeypatch):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for integration tests")

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
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _create_project_and_thread(client: TestClient) -> dict:
    project_payload = {"slug": "demo", "name": "Demo", "settings": {"tier": "dev"}}
    project_resp = client.post("/v1/projects", json=project_payload)
    project_resp.raise_for_status()
    project = project_resp.json()

    thread_payload = {"title": "Hello", "tags": {"topic": "intro"}}
    thread_resp = client.post(
        f"/v1/projects/{project['id']}/threads", json=thread_payload
    )
    thread_resp.raise_for_status()
    return thread_resp.json()


@pytest.mark.integration
def test_approve_idempotent_same_user(client: TestClient):
    thread = _create_project_and_thread(client)

    action_payload = {
        "type": "example",
        "policy_mode": "DRAFT",
        "payload": {"input": "value"},
        "idempotency_key": "idem-approve-idem",
    }
    action_resp = client.post(
        f"/v1/threads/{thread['id']}/actions", json=action_payload
    )
    action_resp.raise_for_status()
    action = action_resp.json()

    first = client.post(
        f"/v1/actions/{action['id']}/approve",
        json={"approved_by": "tester", "channel": "web"},
    )
    assert first.status_code == 200

    second = client.post(
        f"/v1/actions/{action['id']}/approve",
        json={"approved_by": "tester", "channel": "web"},
    )
    assert second.status_code == 200
    assert second.json()["status"] == "APPROVED"


@pytest.mark.integration
def test_approve_conflict_other_user(client: TestClient):
    thread = _create_project_and_thread(client)

    action_payload = {
        "type": "example",
        "policy_mode": "DRAFT",
        "payload": {"input": "value"},
        "idempotency_key": "idem-approve-other",
    }
    action_resp = client.post(
        f"/v1/threads/{thread['id']}/actions", json=action_payload
    )
    action_resp.raise_for_status()
    action = action_resp.json()

    first = client.post(
        f"/v1/actions/{action['id']}/approve",
        json={"approved_by": "tester", "channel": "web"},
    )
    first.raise_for_status()

    second = client.post(
        f"/v1/actions/{action['id']}/approve",
        json={"approved_by": "other", "channel": "web"},
    )
    assert second.status_code == 409
