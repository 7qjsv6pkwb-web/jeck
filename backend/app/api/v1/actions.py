from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Action, Thread
from app.db.session import get_db_session
from app.schemas.actions import ActionApproveRequest, ActionCreate, ActionResponse
from app.services import actions as actions_service

router = APIRouter(tags=["actions"])


@router.post(
    "/threads/{thread_id}/actions",
    response_model=ActionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_action(
    thread_id: UUID, payload: ActionCreate, db: Session = Depends(get_db_session)
) -> ActionResponse:
    thread = db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    action = actions_service.create_action(
        db,
        thread=thread,
        action_type=payload.type,
        policy_mode=payload.policy_mode,
        payload=payload.payload,
        idempotency_key=payload.idempotency_key,
    )
    db.commit()
    db.refresh(action)
    return ActionResponse.model_validate(action)


@router.get("/threads/{thread_id}/actions", response_model=list[ActionResponse])
def list_actions(
    thread_id: UUID, db: Session = Depends(get_db_session)
) -> list[ActionResponse]:
    thread = db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    actions = (
        db.execute(select(Action).where(Action.thread_id == thread_id).order_by(Action.created_at))
        .scalars()
        .all()
    )
    return [ActionResponse.model_validate(action) for action in actions]


@router.get("/actions/{action_id}", response_model=ActionResponse)
def get_action(action_id: UUID, db: Session = Depends(get_db_session)) -> ActionResponse:
    action = db.get(Action, action_id)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")
    return ActionResponse.model_validate(action)


@router.post("/actions/{action_id}/approve", response_model=ActionResponse)
def approve_action(
    action_id: UUID,
    payload: ActionApproveRequest,
    db: Session = Depends(get_db_session),
) -> ActionResponse:
    action = db.get(Action, action_id)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")

    # Web-only approve guardrail
    if payload.channel != "web":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approve can be performed only by a web user.",
        )

    action = actions_service.approve_action(db, action=action, approved_by=payload.approved_by)
    db.commit()
    db.refresh(action)
    return ActionResponse.model_validate(action)