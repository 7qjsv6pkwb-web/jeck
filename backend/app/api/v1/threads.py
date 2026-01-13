from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Project, Thread
from app.db.session import get_db_session
from app.schemas.threads import ThreadCreate, ThreadResponse

router = APIRouter(prefix="/projects/{project_id}/threads", tags=["threads"])


@router.post("", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
def create_thread(
    project_id: UUID, payload: ThreadCreate, db: Session = Depends(get_db_session)
) -> ThreadResponse:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    thread = Thread(project_id=project_id, title=payload.title, tags=payload.tags)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return ThreadResponse.model_validate(thread)


@router.get("", response_model=list[ThreadResponse])
def list_threads(
    project_id: UUID, db: Session = Depends(get_db_session)
) -> list[ThreadResponse]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    threads = (
        db.execute(select(Thread).where(Thread.project_id == project_id).order_by(Thread.created_at))
        .scalars()
        .all()
    )
    return [ThreadResponse.model_validate(thread) for thread in threads]
