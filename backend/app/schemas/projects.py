from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    slug: str
    name: str
    settings: dict = Field(default_factory=dict)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    settings: dict
    created_at: datetime
    updated_at: Optional[datetime]
