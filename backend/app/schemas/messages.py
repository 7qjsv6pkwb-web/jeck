from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    channel: Literal["web", "telegram"]
    role: Literal["user", "assistant", "system"]
    content: str
    meta: dict = Field(default_factory=dict)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: UUID
    channel: str
    role: str
    content: str
    meta: dict
    created_at: datetime
