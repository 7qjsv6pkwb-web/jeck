from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import Action, Thread
from app.schemas.artifacts import ArtifactCreate
from app.services import artifacts as artifact_service
from app.services.executor_contract import ExecutorResult

ExecutorHandler = Callable[[Session, Action], ExecutorResult]

# Registry of action handlers by action.type
HANDLERS: dict[str, ExecutorHandler] = {}


def register_handler(action_type: str, handler: ExecutorHandler) -> None:
    HANDLERS[action_type] = handler


def register(action_type: str) -> Callable[[ExecutorHandler], ExecutorHandler]:
    """Register executor handler for a given action_type."""

    def _decorator(fn: ExecutorHandler) -> ExecutorHandler:
        register_handler(action_type, fn)
        return fn

    return _decorator


def list_handlers() -> list[str]:
    return sorted(HANDLERS.keys())


@register("stub.echo")
def _stub_echo(db: Session, action: Action) -> ExecutorResult:
    return {
        "action_id": str(action.id),
        "type": action.type,
        "status": "executed",
        "data": {"echo": action.payload},
    }

@register("artifact.store")
def _artifact_store(db: Session, action: Action) -> ExecutorResult:
    payload: dict[str, Any] = dict(action.payload or {})
    project_id = _resolve_project_id(db, action, payload)
    thread_id = payload.get("thread_id") or action.thread_id

    artifact_payload = ArtifactCreate(
        project_id=project_id,
        thread_id=thread_id,
        action_id=action.id,
        type=payload["type"],
        filename=payload["filename"],
        content_base64=payload["content_base64"],
        metadata=payload.get("metadata") or {},
    )
    artifact = artifact_service.create_artifact(db, artifact_payload)
    return {
        "action_id": str(action.id),
        "type": action.type,
        "status": "executed",
        "data": {"artifact_id": str(artifact.id)},
    }


def _default_stub(db: Session, action: Action) -> ExecutorResult:
    return {
        "action_id": str(action.id),
        "type": action.type,
        "status": "executed",
        "data": {
            "note": "no handler registered for action.type; default stub used",
            "echo": action.payload,
        },
    }


def execute(db: Session, action: Action) -> ExecutorResult:
    handler = HANDLERS.get(action.type, _default_stub)
    return handler(db, action)


def _resolve_project_id(db: Session, action: Action, payload: dict[str, Any]) -> UUID:
    project_id = payload.get("project_id")
    if project_id:
        return project_id
    thread = db.get(Thread, action.thread_id)
    if not thread:
        raise LookupError("Thread not found")
    return thread.project_id
