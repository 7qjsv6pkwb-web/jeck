import base64
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.db.models import Action, Thread
from app.services import actions as actions_service
from app.services import executor as executor_service


class _StubDB:
    def __init__(self, thread: Thread | None = None):
        self._thread = thread
        self.added = []

    def get(self, model, _id):
        if model is Thread:
            return self._thread
        return None

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        return None

    def commit(self):
        return None

    def refresh(self, _obj):
        return None


def _make_action(*, status: str, policy_mode: str, action_type: str = "stub.echo") -> Action:
    return Action(
        id=uuid.uuid4(),
        thread_id=uuid.uuid4(),
        type=action_type,
        policy_mode=policy_mode,
        status=status,
        payload={"x": 1},
        idempotency_key="unit-1",
    )


def test_executor_dispatches_registered_handler():
    action = _make_action(status="APPROVED", policy_mode="EXECUTE", action_type="unit.test")
    original = dict(executor_service.HANDLERS)
    db = _StubDB()

    def handler(_db: _StubDB, _action: Action):
        return {"action_id": str(_action.id), "type": _action.type, "status": "executed"}

    executor_service.HANDLERS["unit.test"] = handler
    try:
        result = executor_service.execute(db, action)
    finally:
        executor_service.HANDLERS.clear()
        executor_service.HANDLERS.update(original)

    assert result["status"] == "executed"


def test_executor_default_handler_returns_standard_result():
    action = _make_action(status="APPROVED", policy_mode="EXECUTE", action_type="unit.unknown")
    db = _StubDB()
    result = executor_service.execute(db, action)

    assert result["type"] == action.type
    assert result["action_id"] == str(action.id)
    assert result["status"] == "executed"


def test_executor_artifact_store_creates_artifact(monkeypatch):
    thread = Thread(id=uuid.uuid4(), project_id=uuid.uuid4(), title="T", tags={})
    action = _make_action(status="APPROVED", policy_mode="EXECUTE", action_type="artifact.store")
    action.thread_id = thread.id
    action.payload = {
        "type": "report",
        "filename": "hello.txt",
        "content_base64": base64.b64encode(b"hello").decode(),
    }
    db = _StubDB(thread)
    created = {}

    def fake_create_artifact(_db, payload):
        created["payload"] = payload
        return SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr(executor_service.artifact_service, "create_artifact", fake_create_artifact)

    result = executor_service.execute(db, action)

    assert created["payload"].project_id == thread.project_id
    assert created["payload"].thread_id == thread.id
    assert created["payload"].action_id == action.id
    assert result["status"] == "executed"
    assert "artifact_id" in result["data"]


def test_execute_action_blocks_non_approved():
    action = _make_action(status="DRAFT", policy_mode="EXECUTE")
    db = _StubDB()

    with pytest.raises(HTTPException) as exc:
        actions_service.execute_action(db, action=action)

    assert exc.value.status_code == 409


def test_execute_action_persists_result_and_done():
    thread = Thread(id=uuid.uuid4(), project_id=uuid.uuid4(), title="T", tags={})
    action = _make_action(status="APPROVED", policy_mode="EXECUTE", action_type="stub.echo")
    action.thread_id = thread.id
    db = _StubDB(thread)

    result_action = actions_service.execute_action(db, action=action)

    assert result_action.status == "DONE"
    assert result_action.result is not None
