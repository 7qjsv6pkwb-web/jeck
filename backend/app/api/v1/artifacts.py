from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Artifact, Project, Thread, Action
from app.db.session import get_db_session
from app.schemas.artifacts import ArtifactCreate, ArtifactResponse

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.post("", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
def create_artifact(payload: ArtifactCreate, db: Session = Depends(get_db_session)) -> ArtifactResponse:
    # Validate references exist (basic integrity + nicer errors than FK explosions)
    if not db.get(Project, payload.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    if payload.thread_id and not db.get(Thread, payload.thread_id):
        raise HTTPException(status_code=404, detail="Thread not found")
    if payload.action_id and not db.get(Action, payload.action_id):
        raise HTTPException(status_code=404, detail="Action not found")

    artifact = Artifact(
        project_id=payload.project_id,
        thread_id=payload.thread_id,
        action_id=payload.action_id,
        type=payload.type,
        storage_path=payload.storage_path,
        filename=payload.filename,
        metadata_=payload.metadata,
        version=1,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return ArtifactResponse.model_validate(
        {
            "id": artifact.id,
            "project_id": artifact.project_id,
            "thread_id": artifact.thread_id,
            "action_id": artifact.action_id,
            "type": artifact.type,
            "storage_path": artifact.storage_path,
            "filename": artifact.filename,
            "metadata": artifact.metadata_,
            "version": artifact.version,
            "created_at": artifact.created_at,
        }
    )


@router.get("", response_model=list[ArtifactResponse])
def list_artifacts(
    project_id: UUID | None = None,
    thread_id: UUID | None = None,
    action_id: UUID | None = None,
    limit: int = 100,
    db: Session = Depends(get_db_session),
) -> list[ArtifactResponse]:
    q = select(Artifact).order_by(Artifact.created_at.desc()).limit(limit)
    if project_id:
        q = q.where(Artifact.project_id == project_id)
    if thread_id:
        q = q.where(Artifact.thread_id == thread_id)
    if action_id:
        q = q.where(Artifact.action_id == action_id)

    rows = db.execute(q).scalars().all()

    out: list[ArtifactResponse] = []
    for a in rows:
        out.append(
            ArtifactResponse.model_validate(
                {
                    "id": a.id,
                    "project_id": a.project_id,
                    "thread_id": a.thread_id,
                    "action_id": a.action_id,
                    "type": a.type,
                    "storage_path": a.storage_path,
                    "filename": a.filename,
                    "metadata": a.metadata_,
                    "version": a.version,
                    "created_at": a.created_at,
                }
            )
        )
    return out


@router.get("/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(artifact_id: UUID, db: Session = Depends(get_db_session)) -> ArtifactResponse:
    a = db.get(Artifact, artifact_id)
    if not a:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return ArtifactResponse.model_validate(
        {
            "id": a.id,
            "project_id": a.project_id,
            "thread_id": a.thread_id,
            "action_id": a.action_id,
            "type": a.type,
            "storage_path": a.storage_path,
            "filename": a.filename,
            "metadata": a.metadata_,
            "version": a.version,
            "created_at": a.created_at,
        }
    )
