from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.models.provider import ProviderProfile, ProviderDocument
from app.models.service import ProviderService
from app.models.service import Service
from app.models.user import User
from app.models.enums import UserRole, ProviderPresenceStatus
from app.schemas.provider import (
    ProviderProfileResponse,
    ProviderProfileUpdate,
    ProviderStatusUpdate,
    ProviderDocumentCreate,
    ProviderDocumentResponse,
    ProviderServiceCreate,
    ProviderServiceResponse,
    ProviderLocationHeartbeat,
)
from app.api.deps import get_current_user, get_current_provider_profile
from app.services.dispatch_service import DispatchService
import uuid

router = APIRouter()


@router.get("/me", response_model=ProviderProfileResponse)
def get_my_provider_profile(
    profile: ProviderProfile = Depends(get_current_provider_profile)
):
    return profile


@router.patch("/me", response_model=ProviderProfileResponse)
def update_my_provider_profile(
    data: ProviderProfileUpdate,
    profile: ProviderProfile = Depends(get_current_provider_profile),
    db: Session = Depends(get_db)
):
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, val)

    db.commit()
    db.refresh(profile)
    return profile


@router.patch("/me/status", response_model=ProviderProfileResponse)
def update_my_availability(
    data: ProviderStatusUpdate,
    profile: ProviderProfile = Depends(get_current_provider_profile),
    db: Session = Depends(get_db)
):
    if data.is_online is not None:
        profile.is_online = data.is_online
    if data.is_available is not None:
        profile.is_available = data.is_available

    db.commit()
    db.refresh(profile)
    return profile


@router.post("/me/documents", response_model=ProviderDocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_verification_document(
    data: ProviderDocumentCreate,
    profile: ProviderProfile = Depends(get_current_provider_profile),
    db: Session = Depends(get_db)
):
    doc = ProviderDocument(
        provider_id=profile.id,
        document_type=data.document_type,
        document_number=data.document_number,
        file_url=data.file_url
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/me/services", response_model=ProviderServiceResponse, status_code=status.HTTP_201_CREATED)
def add_service_offered(
    data: ProviderServiceCreate,
    profile: ProviderProfile = Depends(get_current_provider_profile),
    db: Session = Depends(get_db)
):
    service = db.query(Service).filter(Service.id == data.service_id).first()
    if not service:
        raise NotFoundException("Service not found")

    existing = db.query(ProviderService).filter(
        ProviderService.provider_id == profile.id,
        ProviderService.service_id == data.service_id
    ).first()

    if existing:
        existing.is_active = data.is_active
        if data.custom_base_charge is not None:
            existing.custom_base_charge = data.custom_base_charge
        db.commit()
        db.refresh(existing)
        return existing

    ps = ProviderService(
        provider_id=profile.id,
        service_id=data.service_id,
        custom_base_charge=data.custom_base_charge,
        is_active=data.is_active
    )
    db.add(ps)
    db.commit()
    db.refresh(ps)
    return ps


@router.get("/nearby", response_model=List[ProviderProfileResponse])
def find_nearby_providers(
    service_id: uuid.UUID = Query(...),
    latitude: float = Query(...),
    longitude: float = Query(...),
    db: Session = Depends(get_db)
):
    results = DispatchService.find_eligible_providers(
        db=db,
        service_id=service_id,
        latitude=latitude,
        longitude=longitude
    )
    return [provider for provider, _ in results]


@router.get("/{provider_id}", response_model=ProviderProfileResponse)
def get_provider_public_profile(
    provider_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    provider = db.query(ProviderProfile).filter(ProviderProfile.id == provider_id).first()
    if not provider:
        raise NotFoundException("Provider not found")
    return provider

@router.post("/me/location")
def update_provider_location(
    data: ProviderLocationHeartbeat,
    profile: ProviderProfile = Depends(get_current_provider_profile),
    db: Session = Depends(get_db)
):
    """
    Heartbeat endpoint for provider live location and presence.
    Updates ephemeral Redis GEO and metadata hash with TTL.
    Validates coordinates.
    """
    if not (-90.0 <= data.latitude <= 90.0 and -180.0 <= data.longitude <= 180.0):
        raise BadRequestException("Invalid latitude or longitude coordinates")

    from app.core.redis import redis_service
    redis_service.update_provider_location(
        provider_id=str(profile.id),
        latitude=data.latitude,
        longitude=data.longitude,
        presence_status=data.presence_status.value,
        service_radius_km=profile.service_radius_km
    )

    # Sync availability to DB model if changed
    if data.presence_status == ProviderPresenceStatus.OFFLINE:
        profile.is_online = False
        profile.is_available = False
    elif data.presence_status == ProviderPresenceStatus.ONLINE_AVAILABLE:
        profile.is_online = True
        profile.is_available = True
    elif data.presence_status == ProviderPresenceStatus.ONLINE_BUSY:
        profile.is_online = True
        profile.is_available = False

    db.commit()

    return {
        "status": "updated",
        "provider_id": str(profile.id),
        "presence_status": data.presence_status.value,
        "latitude": data.latitude,
        "longitude": data.longitude
    }
