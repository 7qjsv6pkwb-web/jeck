from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Message, Thread
from app.db.session import get_db_session
from app.schemas.messages import MessageCreate, MessageResponse

router = APIRouter(prefix="/threads/{thread_id}/messages", tags=["messages"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    thread_id: UUID, payload: MessageCreate, db: Session = Depends(get_db_session)
) -> MessageResponse:
    thread = db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    message = Message(
        thread_id=thread_id,
        channel=payload.channel,
        role=payload.role,
        content=payload.content,
        meta=payload.meta,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return MessageResponse.model_validate(message)


@router.get("", response_model=list[MessageResponse])
def list_messages(
    thread_id: UUID, db: Session = Depends(get_db_session)
) -> list[MessageResponse]:
    thread = db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    messages = (
        db.execute(select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at))
        .scalars()
        .all()
    )
    return [MessageResponse.model_validate(message) for message in messages]
