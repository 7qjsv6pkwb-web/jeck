from __future__ import annotations

from typing import Any, Callable

from app.db.models import Action

ExecutorHandler = Callable[[Action], dict[str, Any]]

# Registry of action handlers by action.type
_HANDLERS: dict[str, ExecutorHandler] = {}


def register(action_type: str) -> Callable[[ExecutorHandler], ExecutorHandler]:
    """Register executor handler for a given action_type."""

    def _decorator(fn: ExecutorHandler) -> ExecutorHandler:
        _HANDLERS[action_type] = fn
        return fn

    return _decorator


def list_handlers() -> list[str]:
    return sorted(_HANDLERS.keys())


@register("stub.echo")
def _stub_echo(action: Action) -> dict[str, Any]:
    return {
        "action_id": str(action.id),
        "type": action.type,
        "echo": action.payload,
    }


def _default_stub(action: Action) -> dict[str, Any]:
    return {
        "action_id": str(action.id),
        "type": action.type,
        "status": "executed",
        "note": "no handler registered for action.type; default stub used",
    }


def execute(action: Action) -> dict[str, Any]:
    handler = _HANDLERS.get(action.type, _default_stub)
    return handler(action)
