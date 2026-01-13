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


@pytest.mark.integration
def test_crud_flow(monkeypatch):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for API smoke tests")

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

    project_payload = {"slug": "demo", "name": "Demo", "settings": {"tier": "dev"}}
    project_response = client.post("/v1/projects", json=project_payload)
    assert project_response.status_code == 201
    project = project_response.json()

    list_projects = client.get("/v1/projects")
    assert list_projects.status_code == 200
    assert len(list_projects.json()) == 1

    get_project = client.get(f"/v1/projects/{project['id']}")
    assert get_project.status_code == 200

    thread_payload = {"title": "Hello", "tags": {"topic": "intro"}}
    thread_response = client.post(
        f"/v1/projects/{project['id']}/threads", json=thread_payload
    )
    assert thread_response.status_code == 201
    thread = thread_response.json()

    list_threads = client.get(f"/v1/projects/{project['id']}/threads")
    assert list_threads.status_code == 200
    assert len(list_threads.json()) == 1

    message_payload = {
        "channel": "web",
        "role": "user",
        "content": "Hello world",
        "meta": {"lang": "en"},
    }
    message_response = client.post(
        f"/v1/threads/{thread['id']}/messages", json=message_payload
    )
    assert message_response.status_code == 201
    message = message_response.json()

    list_messages = client.get(f"/v1/threads/{thread['id']}/messages")
    assert list_messages.status_code == 200
    assert len(list_messages.json()) == 1

    action_payload = {
        "type": "example",
        "policy_mode": "DRAFT",
        "payload": {"input": "value"},
        "idempotency_key": "idem-1",
    }
    action_response = client.post(
        f"/v1/threads/{thread['id']}/actions", json=action_payload
    )
    assert action_response.status_code == 201
    action = action_response.json()
    assert action["status"] == "DRAFT"

    list_actions = client.get(f"/v1/threads/{thread['id']}/actions")
    assert list_actions.status_code == 200
    assert len(list_actions.json()) == 1

    get_action = client.get(f"/v1/actions/{action['id']}")
    assert get_action.status_code == 200
    assert get_action.json()["id"] == action["id"]

    app.dependency_overrides.clear()
