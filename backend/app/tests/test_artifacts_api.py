import base64
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


@pytest.mark.integration
def test_artifacts_flow(monkeypatch, tmp_path):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for integration tests")

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
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

    # Empty list when none
    empty = client.get("/v1/artifacts")
    assert empty.status_code == 200
    assert empty.json() == []

    # Create project + thread + action
    pr = client.post(
        "/v1/projects", json={"slug": "demo", "name": "Demo", "settings": {}}
    )
    assert pr.status_code == 201
    project = pr.json()

    tr = client.post(
        f"/v1/projects/{project['id']}/threads", json={"title": "T1", "tags": {}}
    )
    assert tr.status_code == 201
    thread = tr.json()

    ar = client.post(
        f"/v1/threads/{thread['id']}/actions",
        json={
            "type": "example",
            "policy_mode": "DRAFT",
            "payload": {"x": 1},
            "idempotency_key": "idem-art-1",
        },
    )
    assert ar.status_code == 201
    action = ar.json()

    # Create artifact linked to project+thread+action
    payload = {
        "project_id": project["id"],
        "thread_id": thread["id"],
        "action_id": action["id"],
        "type": "text",
        "filename": "hello.txt",
        "metadata": {"mime": "text/plain"},
        "content_base64": base64.b64encode(b"hello world").decode("ascii"),
    }
    cr = client.post("/v1/artifacts", json=payload)
    assert cr.status_code == 201
    artifact = cr.json()
    assert artifact["project_id"] == project["id"]
    assert artifact["filename"] == "hello.txt"
    stored_path = tmp_path / artifact["storage_path"]
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"hello world"

    # List with filters
    lst = client.get(f"/v1/artifacts?project_id={project['id']}&limit=10")
    assert lst.status_code == 200
    assert len(lst.json()) == 1

    # Get by id
    gt = client.get(f"/v1/artifacts/{artifact['id']}")
    assert gt.status_code == 200
    assert gt.json()["id"] == artifact["id"]

    dl = client.get(f"/v1/artifacts/{artifact['id']}/download")
    assert dl.status_code == 200
    assert dl.content == b"hello world"

    app.dependency_overrides.clear()
