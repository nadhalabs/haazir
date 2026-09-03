from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.models.booking import Booking
from app.models.user import User
from app.models.provider import ProviderProfile
from app.models.enums import BookingStatus, UserRole
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingCancelRequest,
    BookingStatusUpdateRequest
)
from app.api.deps import (
    get_current_user,
    get_current_customer,
    get_current_provider_user,
    get_current_provider_profile
)
from app.services.booking_service import BookingService
import uuid

router = APIRouter()


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    data: BookingCreate,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Creates a new booking using an immutable price quote and address snapshot.
    Client cannot specify prices.
    """
    booking = BookingService.create_booking(
        db=db,
        customer=current_user,
        service_id=data.service_id,
        quote_id=data.quote_id,
        address_id=data.address_id,
        customer_notes=data.customer_notes,
        issue_image_urls=data.issue_image_urls,
        scheduled_for=data.scheduled_for
    )
    return booking


@router.get("", response_model=List[BookingResponse])
def list_my_bookings(
    status_filter: Optional[BookingStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Booking)

    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(Booking.customer_id == current_user.id)
    elif current_user.role == UserRole.PROVIDER:
        provider_profile = db.query(ProviderProfile).filter(ProviderProfile.user_id == current_user.id).first()
        if not provider_profile:
            return []
        query = query.filter(Booking.provider_id == provider_profile.id)
    elif current_user.role == UserRole.ADMIN:
        pass  # Admin can list all

    if status_filter:
        query = query.filter(Booking.status == status_filter)

    return query.order_by(Booking.created_at.desc()).all()


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking_detail(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise NotFoundException("Booking not found")

    # IDOR Protection
    if current_user.role == UserRole.CUSTOMER and booking.customer_id != current_user.id:
        raise ForbiddenException("You are not authorized to view this booking")
    elif current_user.role == UserRole.PROVIDER:
        provider_profile = db.query(ProviderProfile).filter(ProviderProfile.user_id == current_user.id).first()
        if not provider_profile or booking.provider_id != provider_profile.id:
            raise ForbiddenException("You are not authorized to view this booking")

    return booking


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: uuid.UUID,
    data: BookingCancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise NotFoundException("Booking not found")

    return BookingService.transition_status(
        db=db,
        booking=booking,
        to_status=BookingStatus.CANCELLED,
        changed_by_user=current_user,
        reason=data.cancellation_reason
    )


@router.post("/{booking_id}/status", response_model=BookingResponse)
def update_booking_status(
    booking_id: uuid.UUID,
    data: BookingStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise NotFoundException("Booking not found")

    return BookingService.transition_status(
        db=db,
        booking=booking,
        to_status=data.to_status,
        changed_by_user=current_user,
        reason=data.reason,
        metadata=data.metadata
    )


@router.post("/{booking_id}/accept", response_model=BookingResponse)
def accept_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_provider_user),
    profile: ProviderProfile = Depends(get_current_provider_profile),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise NotFoundException("Booking not found")

    return BookingService.assign_provider(
        db=db,
        booking=booking,
        provider=profile,
        assigned_by=current_user
    )

@router.post("/{booking_id}/dispatch", response_model=BookingResponse)
def dispatch_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers dispatch discovery: transitions booking to SEARCHING and dispatches offers.
    Accessible by booking's customer or admin.
    """
    from app.services.dispatch_service import DispatchService
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise NotFoundException("Booking not found")

    if current_user.role == UserRole.CUSTOMER and booking.customer_id != current_user.id:
        raise ForbiddenException("Unauthorized")

    assignments = DispatchService.dispatch_booking(db=db, booking_id=booking_id)
    db.refresh(booking)
    return booking


@router.post("/{booking_id}/reject", status_code=status.HTTP_200_OK)
def reject_booking_offer(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_provider_user),
    db: Session = Depends(get_db)
):
    """
    Provider rejects an offer.
    """
    from app.services.dispatch_service import DispatchService
    assignment = DispatchService.reject_assignment(
        db=db,
        booking_id=booking_id,
        provider_user=current_user
    )
    return {"status": "rejected", "booking_id": str(booking_id)}
