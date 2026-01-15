from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import Audit


def log_audit_event(
    db: Session,
    *,
    actor: str,
    event_type: str,
    payload: dict[str, Any],
    project_id: UUID | None = None,
    thread_id: UUID | None = None,
    action_id: UUID | None = None,
) -> Audit:
    audit = Audit(
        actor=actor,
        event_type=event_type,
        payload=payload,
        project_id=project_id,
        thread_id=thread_id,
        action_id=action_id,
    )
    db.add(audit)
    return audit
