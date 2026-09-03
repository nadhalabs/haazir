from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


class QuoteRequest(BaseModel):
    service_id: uuid.UUID
    is_emergency: bool = False
    provider_id: Optional[uuid.UUID] = None


class PriceQuoteResponse(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    customer_id: uuid.UUID
    base_charge: float
    service_fee: float
    emergency_surcharge: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    currency: str
    is_emergency: bool
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
