from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.enums import SupportCaseStatus


class SupportCaseCreate(BaseModel):
    booking_id: Optional[uuid.UUID] = None
    issue_type: str
    description: str


class SupportCaseUpdate(BaseModel):
    status: Optional[SupportCaseStatus] = None
    resolution_notes: Optional[str] = None


class SupportCaseResponse(BaseModel):
    id: uuid.UUID
    booking_id: Optional[uuid.UUID] = None
    raised_by_user_id: uuid.UUID
    issue_type: str
    description: str
    status: SupportCaseStatus
    resolution_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
