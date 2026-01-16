from __future__ import annotations

from typing import Callable

from app.db.models import Action
from app.services.executor_contract import ExecutorResult

ExecutorHandler = Callable[[Action], ExecutorResult]

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
def _stub_echo(action: Action) -> ExecutorResult:
    return {
        "action_id": str(action.id),
        "type": action.type,
        "status": "executed",
        "data": {"echo": action.payload},
    }


def _default_stub(action: Action) -> ExecutorResult:
    return {
        "action_id": str(action.id),
        "type": action.type,
        "status": "executed",
        "data": {
            "note": "no handler registered for action.type; default stub used",
            "echo": action.payload,
        },
    }


def execute(action: Action) -> ExecutorResult:
    handler = HANDLERS.get(action.type, _default_stub)
    return handler(action)
