from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.core.database import get_db
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.user import User
from app.models.provider import ProviderProfile, ProviderDocument
from app.models.service import ServiceCategory, Service
from app.models.booking import Booking
from app.models.payment import ProviderEarning, Payment
from app.models.support import SupportCase
from app.models.enums import VerificationStatus, PayoutStatus, UserRole, BookingStatus
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


def _provider_payload(provider: ProviderProfile):
    return {
        "id": str(provider.id), "user_id": str(provider.user_id),
        "business_name": provider.business_name, "bio": provider.bio,
        "service_radius_km": provider.service_radius_km,
        "verification_status": provider.verification_status.value,
        "rating_average": provider.rating_average, "rating_count": provider.rating_count,
        "completed_jobs_count": provider.completed_jobs_count,
        "is_online": provider.is_online, "is_available": provider.is_available,
        "user": {"full_name": provider.user.full_name, "phone": provider.user.phone,
                 "email": provider.user.email, "is_active": provider.user.is_active,
                 "is_suspended": provider.user.is_suspended},
        "services": [{"id": str(item.service_id), "name": item.service.name,
                      "is_active": item.is_active} for item in provider.services_offered],
        "documents": [{"id": str(doc.id), "document_type": doc.document_type,
                       "document_number": doc.document_number, "file_url": doc.file_url,
                       "verification_status": doc.verification_status.value} for doc in provider.documents],
    }


@router.get("/dashboard")
def dashboard(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    counts = dict(db.query(Booking.status, func.count(Booking.id)).filter(
        Booking.created_at >= today).group_by(Booking.status).all())
    earnings = db.query(
        func.coalesce(func.sum(ProviderEarning.gross_amount), 0.0),
        func.coalesce(func.sum(ProviderEarning.platform_commission), 0.0),
        func.coalesce(func.sum(ProviderEarning.provider_earning), 0.0),
    ).filter(ProviderEarning.created_at >= today).one()
    return {
        "bookings_today": sum(counts.values()),
        "status_counts": {status.value: counts.get(status, 0) for status in BookingStatus},
        "active_providers": db.query(ProviderProfile).join(User).filter(
            User.is_active.is_(True), User.is_suspended.is_(False),
            ProviderProfile.verification_status == VerificationStatus.VERIFIED).count(),
        "online_providers": db.query(ProviderProfile).join(User).filter(
            User.is_active.is_(True), User.is_suspended.is_(False),
            ProviderProfile.is_online.is_(True)).count(),
        "pending_provider_verification": db.query(ProviderProfile).filter(
            ProviderProfile.verification_status == VerificationStatus.PENDING).count(),
        "gross_booking_value": float(earnings[0]),
        "platform_commission": float(earnings[1]),
        "provider_earnings": float(earnings[2]),
    }


@router.get("/providers")
def list_providers(q: Optional[str] = None, verification_status: Optional[VerificationStatus] = None,
                   admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    query = db.query(ProviderProfile).join(User).options(
        joinedload(ProviderProfile.user), joinedload(ProviderProfile.documents),
        joinedload(ProviderProfile.services_offered))
    if q:
        term = f"%{q}%"
        query = query.filter((User.full_name.ilike(term)) | (User.phone.ilike(term)) |
                             (ProviderProfile.business_name.ilike(term)))
    if verification_status:
        query = query.filter(ProviderProfile.verification_status == verification_status)
    return [_provider_payload(p) for p in query.order_by(ProviderProfile.created_at.desc()).all()]


@router.get("/provider-details/{provider_id}")
def provider_detail(provider_id: uuid.UUID, admin: User = Depends(get_current_admin),
                    db: Session = Depends(get_db)):
    provider = db.query(ProviderProfile).options(joinedload(ProviderProfile.user)).filter(
        ProviderProfile.id == provider_id).first()
    if not provider:
        raise NotFoundException("Provider profile not found")
    return _provider_payload(provider)


@router.get("/customers")
def list_customers(q: Optional[str] = None, admin: User = Depends(get_current_admin),
                   db: Session = Depends(get_db)):
    query = db.query(User).filter(User.role == UserRole.CUSTOMER)
    if q:
        term = f"%{q}%"
        query = query.filter((User.full_name.ilike(term)) | (User.phone.ilike(term)) | (User.email.ilike(term)))
    users = query.order_by(User.created_at.desc()).all()
    return [{"id": str(u.id), "full_name": u.full_name, "phone": u.phone, "email": u.email,
             "is_active": u.is_active, "is_suspended": u.is_suspended, "created_at": u.created_at,
             "booking_count": db.query(Booking).filter(Booking.customer_id == u.id).count()} for u in users]


@router.get("/customers/{customer_id}")
def customer_detail(customer_id: uuid.UUID, admin: User = Depends(get_current_admin),
                    db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == customer_id, User.role == UserRole.CUSTOMER).first()
    if not user:
        raise NotFoundException("Customer not found")
    return {"customer": UserResponse.model_validate(user),
            "bookings": [b for b in db.query(Booking).filter(Booking.customer_id == user.id)
                         .order_by(Booking.created_at.desc()).all()]}


@router.get("/bookings")
def operations_bookings(status_filter: Optional[BookingStatus] = Query(None, alias="status"),
                        booking_number: Optional[str] = None, customer_id: Optional[uuid.UUID] = None,
                        provider_id: Optional[uuid.UUID] = None, service_id: Optional[uuid.UUID] = None,
                        admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    query = db.query(Booking).options(joinedload(Booking.customer), joinedload(Booking.provider))
    for column, value in ((Booking.status, status_filter), (Booking.customer_id, customer_id),
                          (Booking.provider_id, provider_id), (Booking.service_id, service_id)):
        if value is not None:
            query = query.filter(column == value)
    if booking_number:
        query = query.filter(Booking.booking_number.ilike(f"%{booking_number}%"))
    return query.order_by(Booking.created_at.desc()).all()


@router.get("/payments")
def payment_visibility(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    payments = db.query(Payment).options(joinedload(Payment.booking)).order_by(Payment.created_at.desc()).all()
    return [{"id": str(p.id), "booking_id": str(p.booking_id),
             "booking_number": p.booking.booking_number, "amount": p.amount, "currency": p.currency,
             "payment_method": p.payment_method.value, "status": p.status.value,
             "completed_at": p.booking.completed_at,
             "platform_commission": p.booking.earning.platform_commission if p.booking.earning else None,
             "provider_earning": p.booking.earning.provider_earning if p.booking.earning else None} for p in payments]


@router.get("/catalog")
def catalog(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return {"categories": db.query(ServiceCategory).order_by(ServiceCategory.display_order).all(),
            "services": db.query(Service).order_by(Service.name).all()}


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
    if data.role is not None and data.role != user.role:
        raise BadRequestException("Role changes are not supported by account moderation")

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
