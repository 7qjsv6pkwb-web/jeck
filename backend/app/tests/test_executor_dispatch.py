import uuid
from dataclasses import dataclass

from app.services import executor


@dataclass
class FakeAction:
    id: uuid.UUID
    type: str
    payload: dict


def test_executor_dispatch_known_handler():
    action = FakeAction(id=uuid.uuid4(), type="stub.echo", payload={"x": 1})
    result = executor.execute(action)  # type: ignore[arg-type]
    assert result["type"] == "stub.echo"
    assert result["action_id"] == str(action.id)
    assert result["echo"] == {"x": 1}


def test_executor_dispatch_default_handler():
    action = FakeAction(id=uuid.uuid4(), type="unknown.type", payload={"x": 1})
    result = executor.execute(action)  # type: ignore[arg-type]
    assert result["type"] == "unknown.type"
    assert result["action_id"] == str(action.id)
    assert result["status"] == "executed"
