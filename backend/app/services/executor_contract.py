from __future__ import annotations

from typing import Any, Protocol, TypedDict

from app.db.models import Action


class ExecutorResult(TypedDict, total=False):
    type: str
    action_id: str
    status: str
    data: dict[str, Any]
    error: str


class Executor(Protocol):
    def execute(self, action: Action) -> ExecutorResult:
        ...

