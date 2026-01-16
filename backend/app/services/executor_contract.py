from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.db.models import Action


@dataclass(frozen=True)
class ExecutorResult:
    ok: bool
    data: dict[str, Any]


class Executor(Protocol):
    def execute(self, action: Action) -> ExecutorResult:
        ...


