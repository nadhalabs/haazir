from typing import Optional, List
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.enums import VerificationStatus, ProviderPresenceStatus
from app.schemas.service import ServiceResponse


class ProviderDocumentBase(BaseModel):
    document_type: str
    document_number: Optional[str] = None
    file_url: str


class ProviderDocumentCreate(ProviderDocumentBase):
    pass


class ProviderDocumentResponse(ProviderDocumentBase):
    id: uuid.UUID
    verification_status: VerificationStatus

    model_config = ConfigDict(from_attributes=True)


class ProviderServiceCreate(BaseModel):
    service_id: uuid.UUID
    custom_base_charge: Optional[float] = None
    is_active: bool = True


class ProviderServiceResponse(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    custom_base_charge: Optional[float] = None
    is_active: bool
    service: Optional[ServiceResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProviderProfileBase(BaseModel):
    business_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    service_radius_km: float = 15.0
    base_latitude: Optional[float] = None
    base_longitude: Optional[float] = None


class ProviderProfileCreate(ProviderProfileBase):
    pass


class ProviderProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    service_radius_km: Optional[float] = None
    base_latitude: Optional[float] = None
    base_longitude: Optional[float] = None


class ProviderStatusUpdate(BaseModel):
    is_online: Optional[bool] = None
    is_available: Optional[bool] = None


class ProviderVerificationUpdate(BaseModel):
    verification_status: VerificationStatus


class ProviderProfileResponse(ProviderProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    verification_status: VerificationStatus
    is_online: bool
    is_available: bool
    rating_average: float
    rating_count: int
    completed_jobs_count: int
    services_offered: List[ProviderServiceResponse] = []
    documents: List[ProviderDocumentResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ProviderLocationHeartbeat(BaseModel):
    latitude: float
    longitude: float
    presence_status: ProviderPresenceStatus = ProviderPresenceStatus.ONLINE_AVAILABLE


class ProviderRejectOfferRequest(BaseModel):
    reason: Optional[str] = None
