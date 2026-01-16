from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.artifacts import ArtifactCreate, ArtifactResponse
from app.services import artifacts as artifact_service

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.post("", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
def create_artifact(
    payload: ArtifactCreate, db: Session = Depends(get_db_session)
) -> ArtifactResponse:
    try:
        artifact = artifact_service.create_artifact(db, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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
    rows = artifact_service.list_artifacts(
        db, project_id=project_id, thread_id=thread_id, action_id=action_id, limit=limit
    )

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
def get_artifact(
    artifact_id: UUID, db: Session = Depends(get_db_session)
) -> ArtifactResponse:
    a = artifact_service.get_artifact(db, artifact_id)
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


@router.get("/{artifact_id}/download")
def download_artifact(
    artifact_id: UUID, db: Session = Depends(get_db_session)
) -> FileResponse:
    artifact = artifact_service.get_artifact(db, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    file_path = artifact_service.get_artifact_file_path(artifact)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Artifact file not found")

    return FileResponse(path=file_path, filename=artifact.filename)
