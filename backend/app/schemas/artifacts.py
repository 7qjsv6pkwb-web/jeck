from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ArtifactCreate(BaseModel):
    project_id: UUID
    thread_id: Optional[UUID] = None
    action_id: Optional[UUID] = None
    type: str
    filename: str
    metadata: dict = Field(default_factory=dict)
    content_base64: str


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    thread_id: Optional[UUID]
    action_id: Optional[UUID]
    type: str
    storage_path: str
    filename: str
    metadata: dict
    version: int
    created_at: datetime
