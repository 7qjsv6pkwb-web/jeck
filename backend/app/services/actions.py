from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Action, Thread
from app.services import audit as audit_service
from app.services import executor as executor_service


ALLOWED_TRANSITIONS = {
    "DRAFT": {"APPROVED", "CANCELED"},
    "APPROVED": {"EXECUTING", "CANCELED"},
    "EXECUTING": {"DONE", "FAILED"},
}


def create_action(
    db: Session,
    *,
    thread: Thread,
    action_type: str,
    policy_mode: str,
    payload: dict[str, Any],
    idempotency_key: str,
    actor: str = "system",
) -> Action:
    action = Action(
        thread_id=thread.id,
        type=action_type,
        policy_mode=policy_mode,
        status="DRAFT",
        payload=payload,
        idempotency_key=idempotency_key,
    )
    db.add(action)
    db.flush()
    audit_service.log_audit_event(
        db,
        actor=actor,
        event_type="action.created",
        payload={"status": action.status},
        project_id=thread.project_id,
        thread_id=thread.id,
        action_id=action.id,
    )
    return action


def approve_action(db: Session, *, action: Action, approved_by: str) -> Action:
    # Idempotent approve: same approver can repeat approve safely
    if action.status == "APPROVED":
        if action.approved_by == approved_by:
            return action
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Action already approved by another user.",
        )

    _transition_action(db, action, "APPROVED", actor=approved_by)
    action.approved_by = approved_by
    return action

def cancel_action(db: Session, *, action: Action, actor: str = "system") -> Action:
    _transition_action(db, action, "CANCELED", actor=actor)
    return action


def execute_action(db: Session, *, action: Action) -> Action:
    if action.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Action must be APPROVED before execution.",
        )
    if action.policy_mode != "EXECUTE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Action policy_mode must be EXECUTE to run.",
        )
    thread = db.get(Thread, action.thread_id)
    project_id = thread.project_id if thread else None
    audit_service.log_audit_event(
        db,
        actor="system",
        event_type="action.execute_attempt",
        payload={"status": action.status},
        project_id=project_id,
        thread_id=action.thread_id,
        action_id=action.id,
    )
    _transition_action(db, action, "EXECUTING", actor="system")
    try:
        result = executor_service.execute(db, action)
        action.result = result
        _transition_action(db, action, "DONE", actor="system")
        audit_service.log_audit_event(
            db,
            actor="system",
            event_type="action.execute_succeeded",
            payload={"status": action.status},
            project_id=project_id,
            thread_id=action.thread_id,
            action_id=action.id,
        )
    except Exception as exc:  # noqa: BLE001
        action.result = {"error": str(exc)}
        _transition_action(db, action, "FAILED", actor="system")
        audit_service.log_audit_event(
            db,
            actor="system",
            event_type="action.execute_failed",
            payload={"status": action.status, "error": str(exc)},
            project_id=project_id,
            thread_id=action.thread_id,
            action_id=action.id,
        )
    return action


def _transition_action(db: Session, action: Action, new_status: str, *, actor: str) -> None:
    allowed = ALLOWED_TRANSITIONS.get(action.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid transition from {action.status} to {new_status}.",
        )
    action.status = new_status
    thread = db.get(Thread, action.thread_id)
    project_id = thread.project_id if thread else None
    audit_service.log_audit_event(
        db,
        actor=actor,
        event_type=f"action.{new_status.lower()}",
        payload={"status": new_status},
        project_id=project_id,
        thread_id=action.thread_id,
        action_id=action.id,
    )
