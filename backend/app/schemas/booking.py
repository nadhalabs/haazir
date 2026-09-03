from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.enums import BookingStatus, AssignmentStatus
from app.schemas.pricing import PriceQuoteResponse
from app.schemas.payment import PaymentResponse, ProviderEarningResponse
from app.schemas.rating import RatingResponse


class BookingCreate(BaseModel):
    service_id: uuid.UUID
    quote_id: uuid.UUID
    address_id: uuid.UUID
    customer_notes: Optional[str] = None
    issue_image_urls: List[str] = []
    scheduled_for: Optional[datetime] = None


class BookingCancelRequest(BaseModel):
    cancellation_reason: str


class BookingStatusUpdateRequest(BaseModel):
    to_status: BookingStatus
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BookingAssignmentResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    provider_id: uuid.UUID
    status: AssignmentStatus
    response_time_seconds: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingStatusHistoryResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    from_status: Optional[BookingStatus] = None
    to_status: BookingStatus
    changed_by_user_id: Optional[uuid.UUID] = None
    reason: Optional[str] = None
    metadata_json: Dict[str, Any] = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    id: uuid.UUID
    booking_number: str
    customer_id: uuid.UUID
    provider_id: Optional[uuid.UUID] = None
    service_id: uuid.UUID
    quote_id: uuid.UUID
    status: BookingStatus
    customer_notes: Optional[str] = None
    issue_image_urls: List[str] = []
    address_snapshot: Dict[str, Any]
    service_snapshot: Dict[str, Any]
    provider_snapshot: Optional[Dict[str, Any]] = None

    scheduled_for: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    cancelled_by_user_id: Optional[uuid.UUID] = None
    created_at: datetime

    price_quote: Optional[PriceQuoteResponse] = None
    payment: Optional[PaymentResponse] = None
    earning: Optional[ProviderEarningResponse] = None
    rating: Optional[RatingResponse] = None
    assignments: List[BookingAssignmentResponse] = []
    status_history: List[BookingStatusHistoryResponse] = []

    model_config = ConfigDict(from_attributes=True)
