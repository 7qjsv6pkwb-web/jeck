import base64
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
def test_execute_sets_result_and_done(monkeypatch, tmp_path):
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

    project = client.post("/v1/projects", json={"slug": "demo", "name": "Demo", "settings": {}}).json()
    thread = client.post(f"/v1/projects/{project['id']}/threads", json={"title": "Hello", "tags": {}}).json()

    action = client.post(
        f"/v1/threads/{thread['id']}/actions",
        json={"type": "stub", "policy_mode": "EXECUTE", "payload": {"x": 1}, "idempotency_key": "idem-exec-1"},
    ).json()

    client.post(f"/v1/actions/{action['id']}/approve", json={"approved_by": "tester", "channel": "web"}).raise_for_status()

    executed = client.post(f"/v1/actions/{action['id']}/execute")
    executed.raise_for_status()
    body = executed.json()

    assert body["status"] == "DONE"
    assert body["result"] is not None
    assert body["result"]["type"] == "stub"
    assert "action_id" in body["result"]
    assert body["result"]["status"] == "executed"

    artifact_action = client.post(
        f"/v1/threads/{thread['id']}/actions",
        json={
            "type": "artifact.store",
            "policy_mode": "EXECUTE",
            "payload": {
                "type": "report",
                "filename": "note.txt",
                "content_base64": base64.b64encode(b"artifact").decode(),
            },
            "idempotency_key": "idem-artifact-1",
        },
    ).json()
    client.post(
        f"/v1/actions/{artifact_action['id']}/approve",
        json={"approved_by": "tester", "channel": "web"},
    ).raise_for_status()
    executed_artifact = client.post(f"/v1/actions/{artifact_action['id']}/execute")
    executed_artifact.raise_for_status()
    artifact_body = executed_artifact.json()

    assert artifact_body["status"] == "DONE"
    assert artifact_body["result"]["type"] == "artifact.store"
    artifact_id = artifact_body["result"]["data"]["artifact_id"]

    artifacts = client.get(f"/v1/artifacts?action_id={artifact_action['id']}&limit=5")
    artifacts.raise_for_status()
    rows = artifacts.json()
    assert len(rows) == 1
    assert rows[0]["id"] == artifact_id
    stored_path = tmp_path / rows[0]["storage_path"]
    assert stored_path.exists()

    audit = client.get(f"/v1/audit?action_id={action['id']}&limit=50")
    audit.raise_for_status()
    event_types = {row["event_type"] for row in audit.json()}
    assert "action.execute_attempt" in event_types

    audit = client.get(f"/v1/audit?action_id={action['id']}&limit=50")
    audit.raise_for_status()
    event_types = {row["event_type"] for row in audit.json()}
    assert "action.execute_attempt" in event_types

    app.dependency_overrides.clear()
