from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Audit
from app.db.session import get_db_session
from app.schemas.audit import AuditResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditResponse])
def list_audit(
    project_id: UUID | None = None,
    thread_id: UUID | None = None,
    action_id: UUID | None = None,
    limit: int = 100,
    db: Session = Depends(get_db_session),
) -> list[AuditResponse]:
    q = select(Audit).order_by(Audit.created_at.desc()).limit(limit)

    if project_id:
        q = q.where(Audit.project_id == project_id)
    if thread_id:
        q = q.where(Audit.thread_id == thread_id)
    if action_id:
        q = q.where(Audit.action_id == action_id)

    rows = db.execute(q).scalars().all()
    return [AuditResponse.model_validate(r) for r in rows]
