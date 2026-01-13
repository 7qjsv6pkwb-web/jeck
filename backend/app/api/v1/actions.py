from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Action, Thread
from app.db.session import get_db_session
from app.schemas.actions import ActionCreate, ActionResponse

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
    action = Action(
        thread_id=thread_id,
        type=payload.type,
        policy_mode=payload.policy_mode,
        status="DRAFT",
        payload=payload.payload,
        idempotency_key=payload.idempotency_key,
    )
    db.add(action)
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
