from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.user import User
from app.models.enums import UserRole, BookingStatus, PaymentStatus
from app.schemas.payment import (
    PaymentCreate,
    PaymentProcessRequest,
    PaymentResponse
)
from app.api.deps import get_current_user, get_current_customer
from app.services.payment_service import PaymentService
import uuid

router = APIRouter()


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def initiate_payment(
    data: PaymentCreate,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == data.booking_id).first()
    if not booking:
        raise NotFoundException("Booking not found")

    if booking.customer_id != current_user.id:
        raise ForbiddenException("Booking does not belong to you")

    return PaymentService.create_payment_for_booking(
        db=db,
        booking=booking,
        payment_method=data.payment_method
    )


@router.post("/{payment_id}/complete", response_model=PaymentResponse)
def confirm_payment_completion(
    payment_id: uuid.UUID,
    data: PaymentProcessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirms payment receipt (e.g. Cash collected by provider, or webhook confirmation).
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise NotFoundException("Payment record not found")

    booking = payment.booking
    if booking.status != BookingStatus.COMPLETED:
        raise BadRequestException("Payment can only be confirmed after the job is completed")
    # Ensure only assigned provider or admin can confirm cash payment
    if current_user.role == UserRole.PROVIDER:
        if not booking.provider or booking.provider.user_id != current_user.id:
            raise ForbiddenException("You are not authorized to mark this payment as received")
    elif current_user.role != UserRole.ADMIN:
        raise ForbiddenException("Only provider or admin can complete payment collection")

    return PaymentService.mark_payment_successful(
        db=db,
        payment=payment,
        transaction_reference=data.transaction_reference
    )


@router.get("/booking/{booking_id}", response_model=PaymentResponse)
def get_payment_for_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
    if not payment:
        raise NotFoundException("Payment not found for this booking")

    booking = payment.booking
    if current_user.role == UserRole.CUSTOMER and booking.customer_id != current_user.id:
        raise ForbiddenException("Unauthorized")
    elif current_user.role == UserRole.PROVIDER and (not booking.provider or booking.provider.user_id != current_user.id):
        raise ForbiddenException("Unauthorized")

    return payment
