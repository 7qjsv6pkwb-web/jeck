from __future__ import annotations

from typing import Callable

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
def _stub_echo(_db: Session, action: Action) -> ExecutorResult:
    return {
        "action_id": str(action.id),
        "type": action.type,
        "status": "executed",
        "data": {"echo": action.payload},
    }


@register("artifact.store")
def _artifact_store(db: Session, action: Action) -> ExecutorResult:
    """Persist an artifact referenced by action payload.

    Expected payload schema:
    {
        "project_id": "<uuid>",
        "thread_id": "<uuid>",  # optional (defaults to action.thread_id)
        "type": "<artifact type>",
        "filename": "<filename>",
        "metadata": {},  # optional
        "content_base64": "<base64>"
    }
    """
    payload = dict(action.payload or {})
    if "thread_id" not in payload:
        payload["thread_id"] = action.thread_id
    if "action_id" not in payload:
        payload["action_id"] = action.id
    if "metadata" not in payload:
        payload["metadata"] = {}
    if "project_id" not in payload:
        thread = db.get(Thread, action.thread_id)
        if thread:
            payload["project_id"] = thread.project_id

    artifact_payload = ArtifactCreate(**payload)
    artifact = artifact_service.create_artifact(db, artifact_payload)
    return {
        "action_id": str(action.id),
        "type": action.type,
        "status": "executed",
        "data": {"artifact_id": str(artifact.id)},
    }


def _default_stub(_db: Session, action: Action) -> ExecutorResult:
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
