from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.user import User
from app.models.provider import ProviderProfile, ProviderDocument
from app.models.service import ServiceCategory, Service
from app.models.booking import Booking
from app.models.payment import ProviderEarning
from app.models.enums import VerificationStatus, PayoutStatus, UserRole
from app.schemas.user import UserResponse, AdminUserUpdate
from app.schemas.provider import ProviderProfileResponse, ProviderVerificationUpdate
from app.schemas.service import (
    ServiceCategoryCreate,
    ServiceCategoryUpdate,
    ServiceCategoryResponse,
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse
)
from app.schemas.payment import ProviderEarningResponse
from app.api.deps import get_current_admin
import uuid

router = APIRouter()


# --- User & Account Moderation ---

@router.get("/users", response_model=List[UserResponse])
def list_all_users(
    role: Optional[UserRole] = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()


@router.patch("/users/{user_id}", response_model=UserResponse)
def moderate_user(
    user_id: uuid.UUID,
    data: AdminUserUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User not found")

    if data.is_active is not None:
        user.is_active = data.is_active
    if data.is_suspended is not None:
        user.is_suspended = data.is_suspended
    if data.role is not None:
        user.role = data.role

    db.commit()
    db.refresh(user)
    return user


# --- Provider Verification (V1 Admin Verification) ---

@router.get("/providers/pending", response_model=List[ProviderProfileResponse])
def list_pending_providers(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return db.query(ProviderProfile).filter(
        ProviderProfile.verification_status == VerificationStatus.PENDING
    ).all()


@router.patch("/providers/{provider_id}/verify", response_model=ProviderProfileResponse)
def update_provider_verification(
    provider_id: uuid.UUID,
    data: ProviderVerificationUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    provider = db.query(ProviderProfile).filter(ProviderProfile.id == provider_id).first()
    if not provider:
        raise NotFoundException("Provider profile not found")

    provider.verification_status = data.verification_status
    db.commit()
    db.refresh(provider)
    return provider


# --- Service Catalog Administration ---

@router.post("/categories", response_model=ServiceCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_service_category(
    data: ServiceCategoryCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    cat = ServiceCategory(
        name=data.name,
        slug=data.slug,
        description=data.description,
        icon_url=data.icon_url,
        is_active=data.is_active,
        display_order=data.display_order
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.patch("/categories/{category_id}", response_model=ServiceCategoryResponse)
def update_service_category(
    category_id: uuid.UUID,
    data: ServiceCategoryUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    cat = db.query(ServiceCategory).filter(ServiceCategory.id == category_id).first()
    if not cat:
        raise NotFoundException("Service category not found")

    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(cat, field, val)

    db.commit()
    db.refresh(cat)
    return cat


@router.post("/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(
    data: ServiceCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    service = Service(
        category_id=data.category_id,
        name=data.name,
        slug=data.slug,
        description=data.description,
        estimated_duration_mins=data.estimated_duration_mins,
        base_visit_charge=data.base_visit_charge,
        min_charge=data.min_charge,
        emergency_surcharge_rate=data.emergency_surcharge_rate,
        is_active=data.is_active
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.patch("/services/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: uuid.UUID,
    data: ServiceUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise NotFoundException("Service not found")

    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(service, field, val)

    db.commit()
    db.refresh(service)
    return service


# --- Provider Earnings & Payout Management ---

@router.get("/earnings", response_model=List[ProviderEarningResponse])
def list_earnings(
    payout_status: Optional[PayoutStatus] = Query(None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(ProviderEarning)
    if payout_status:
        query = query.filter(ProviderEarning.payout_status == payout_status)
    return query.all()


@router.post("/earnings/{earning_id}/process-payout", response_model=ProviderEarningResponse)
def process_earning_payout(
    earning_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    earning = db.query(ProviderEarning).filter(ProviderEarning.id == earning_id).first()
    if not earning:
        raise NotFoundException("Provider earning record not found")

    earning.payout_status = PayoutStatus.PROCESSED
    db.commit()
    db.refresh(earning)
    return earning
