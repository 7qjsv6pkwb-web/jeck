from __future__ import annotations

from app.db.models import Action
from app.services.executor_contract import ExecutorResult


def execute(action: Action) -> dict:
    # stub executor (MVP): always succeeds and returns minimal payload
    result = ExecutorResult(
        ok=True,
        data={
            "action_id": str(action.id),
            "type": action.type,
            "status": "executed",
        },
    )
    return result.data
