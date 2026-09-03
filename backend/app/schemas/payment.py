from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.enums import PaymentMethod, PaymentStatus, PayoutStatus


class PaymentCreate(BaseModel):
    booking_id: uuid.UUID
    payment_method: PaymentMethod


class PaymentProcessRequest(BaseModel):
    transaction_reference: Optional[str] = None


class PaymentResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    amount: float
    currency: str
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_reference: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProviderEarningResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    provider_id: uuid.UUID
    gross_amount: float
    platform_commission: float
    provider_earning: float
    payout_status: PayoutStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
