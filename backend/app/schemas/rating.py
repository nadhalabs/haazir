from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


class RatingCreate(BaseModel):
    booking_id: uuid.UUID
    score: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None


class RatingResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    customer_id: uuid.UUID
    provider_id: uuid.UUID
    score: int
    review_text: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
