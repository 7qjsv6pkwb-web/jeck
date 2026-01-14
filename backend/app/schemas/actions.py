from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ActionCreate(BaseModel):
    type: str
    policy_mode: Literal["READ", "DRAFT", "EXECUTE"]
    payload: dict = Field(default_factory=dict)
    idempotency_key: str


class ActionApproveRequest(BaseModel):
    approved_by: str
    channel: Literal["web", "telegram"] = "web"


class ActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: UUID
    type: str
    policy_mode: str
    status: str
    payload: dict
    result: Optional[dict]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    idempotency_key: str
    created_at: datetime
    updated_at: Optional[datetime]
