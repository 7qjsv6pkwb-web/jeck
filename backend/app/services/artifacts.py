import base64
import binascii
import os
from pathlib import Path
from typing import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Action, Artifact, Project, Thread
from app.schemas.artifacts import ArtifactCreate

ARTIFACTS_DIR_ENV = "ARTIFACTS_DIR"


def get_storage_root() -> Path:
    return Path(os.getenv(ARTIFACTS_DIR_ENV, "artifacts_storage"))


def build_storage_path(project_id: UUID, artifact_id: UUID, filename: str) -> Path:
    safe_name = Path(filename).name
    return Path("artifacts") / str(project_id) / str(artifact_id) / safe_name


def decode_content(content_base64: str) -> bytes:
    try:
        return base64.b64decode(content_base64, validate=True)
    except binascii.Error as exc:
        raise ValueError("Invalid content_base64 payload") from exc


def write_artifact_bytes(storage_root: Path, relative_path: Path, content: bytes) -> None:
    target_path = storage_root / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(content)


def create_artifact(db: Session, payload: ArtifactCreate) -> Artifact:
    if not db.get(Project, payload.project_id):
        raise LookupError("Project not found")
    if payload.thread_id and not db.get(Thread, payload.thread_id):
        raise LookupError("Thread not found")
    if payload.action_id and not db.get(Action, payload.action_id):
        raise LookupError("Action not found")

    artifact = Artifact(
        project_id=payload.project_id,
        thread_id=payload.thread_id,
        action_id=payload.action_id,
        type=payload.type,
        storage_path="",
        filename=payload.filename,
        metadata_=payload.metadata,
        version=1,
    )
    db.add(artifact)
    db.flush()

    relative_path = build_storage_path(payload.project_id, artifact.id, payload.filename)
    write_artifact_bytes(get_storage_root(), relative_path, decode_content(payload.content_base64))
    artifact.storage_path = relative_path.as_posix()

    db.commit()
    db.refresh(artifact)
    return artifact


def list_artifacts(
    db: Session,
    project_id: UUID | None = None,
    thread_id: UUID | None = None,
    action_id: UUID | None = None,
    limit: int = 100,
) -> Iterable[Artifact]:
    query = select(Artifact).order_by(Artifact.created_at.desc()).limit(limit)
    if project_id:
        query = query.where(Artifact.project_id == project_id)
    if thread_id:
        query = query.where(Artifact.thread_id == thread_id)
    if action_id:
        query = query.where(Artifact.action_id == action_id)
    return db.execute(query).scalars().all()


def get_artifact(db: Session, artifact_id: UUID) -> Artifact | None:
    return db.get(Artifact, artifact_id)


def get_artifact_file_path(artifact: Artifact) -> Path:
    return get_storage_root() / Path(artifact.storage_path)
