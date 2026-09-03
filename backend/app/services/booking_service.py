from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException,
    ConflictException
)
from app.models.booking import Booking, BookingAssignment, BookingStatusHistory
from app.models.enums import (
    BookingStatus,
    AssignmentStatus,
    UserRole,
    PaymentStatus,
    ProviderPresenceStatus
)
from app.models.user import User
from app.models.address import Address
from app.models.provider import ProviderProfile
from app.models.service import Service
from app.models.pricing import PriceQuote
from app.services.pricing_service import PricingService
from app.core.redis import redis_service
import uuid
import random


class BookingService:
    # Explicit Allowed State Transitions
    VALID_TRANSITIONS = {
        BookingStatus.REQUESTED: [BookingStatus.SEARCHING, BookingStatus.ASSIGNED, BookingStatus.CANCELLED, BookingStatus.FAILED],
        BookingStatus.SEARCHING: [BookingStatus.ASSIGNED, BookingStatus.CANCELLED, BookingStatus.FAILED],
        BookingStatus.ASSIGNED: [BookingStatus.PROVIDER_EN_ROUTE, BookingStatus.CANCELLED, BookingStatus.FAILED],
        BookingStatus.PROVIDER_EN_ROUTE: [BookingStatus.ARRIVED, BookingStatus.CANCELLED],
        BookingStatus.ARRIVED: [BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED],
        BookingStatus.IN_PROGRESS: [BookingStatus.COMPLETED, BookingStatus.FAILED],
        BookingStatus.COMPLETED: [],  # Terminal state
        BookingStatus.CANCELLED: [],  # Terminal state
        BookingStatus.FAILED: []      # Terminal state
    }

    @staticmethod
    def generate_booking_number() -> str:
        date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_part = f"{random.randint(1000, 9999)}"
        return f"HZ-{date_part}-{rand_part}"

    @classmethod
    def create_booking(
        cls,
        db: Session,
        customer: User,
        service_id: uuid.UUID,
        quote_id: uuid.UUID,
        address_id: uuid.UUID,
        customer_notes: Optional[str] = None,
        issue_image_urls: Optional[List[str]] = None,
        scheduled_for: Optional[datetime] = None
    ) -> Booking:
        # Validate Customer ownership and lock quote
        quote = PricingService.validate_and_lock_quote(db, quote_id=quote_id, customer_id=customer.id)

        # Validate Address ownership
        address = db.query(Address).filter(Address.id == address_id).first()
        if not address:
            raise NotFoundException("Address not found")
        if address.user_id != customer.id:
            raise ForbiddenException("Address does not belong to the current customer")

        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise NotFoundException("Service not found")
        if quote.service_id != service.id:
            raise BadRequestException("Quote does not match the requested service")
        if not service.is_active:
            raise BadRequestException("Service is not currently available")

        # Snapshot address and service at booking time
        address_snapshot = {
            "address_id": str(address.id),
            "label": address.label,
            "address_line1": address.address_line1,
            "address_line2": address.address_line2,
            "city": address.city,
            "state": address.state,
            "postal_code": address.postal_code,
            "latitude": address.latitude,
            "longitude": address.longitude,
        }

        service_snapshot = {
            "service_id": str(service.id),
            "name": service.name,
            "category_id": str(service.category_id),
            "base_visit_charge": service.base_visit_charge,
            "emergency_surcharge_rate": service.emergency_surcharge_rate,
            "estimated_duration_mins": service.estimated_duration_mins,
        }

        booking = Booking(
            booking_number=cls.generate_booking_number(),
            customer_id=customer.id,
            service_id=service.id,
            quote_id=quote.id,
            status=BookingStatus.REQUESTED,
            customer_notes=customer_notes,
            issue_image_urls=issue_image_urls or [],
            address_snapshot=address_snapshot,
            service_snapshot=service_snapshot,
            scheduled_for=scheduled_for
        )

        db.add(booking)
        db.flush()

        # Add initial status history
        history = BookingStatusHistory(
            booking_id=booking.id,
            from_status=None,
            to_status=BookingStatus.REQUESTED,
            changed_by_user_id=customer.id,
            reason="Booking requested by customer",
            metadata_json={"quote_id": str(quote.id)}
        )
        db.add(history)
        db.commit()
        db.refresh(booking)
        return booking

    @classmethod
    def transition_status(
        cls,
        db: Session,
        booking: Booking,
        to_status: BookingStatus,
        changed_by_user: User,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Booking:
        from_status = booking.status

        # Validate transition legality
        allowed = cls.VALID_TRANSITIONS.get(from_status, [])
        if to_status not in allowed:
            raise BadRequestException(
                f"Illegal state transition from {from_status.value} to {to_status.value}"
            )

        # Enforce RBAC rules on status changes
        if changed_by_user.role == UserRole.CUSTOMER:
            if booking.customer_id != changed_by_user.id:
                raise ForbiddenException("Cannot modify booking for another customer")
            if to_status not in [BookingStatus.SEARCHING, BookingStatus.CANCELLED]:
                raise ForbiddenException("Customers can only search for providers or cancel a booking")

        elif changed_by_user.role == UserRole.PROVIDER:
            if not booking.provider_id or booking.provider.user_id != changed_by_user.id:
                raise ForbiddenException("Cannot modify booking not assigned to you")
            if to_status in [BookingStatus.REQUESTED, BookingStatus.SEARCHING]:
                raise ForbiddenException("Providers cannot revert booking to searching/requested")

        now = datetime.now(timezone.utc)
        booking.status = to_status

        if to_status == BookingStatus.IN_PROGRESS and not booking.started_at:
            booking.started_at = now
        elif to_status == BookingStatus.COMPLETED:
            booking.completed_at = now
            # Update provider stats
            if booking.provider:
                booking.provider.completed_jobs_count += 1
                booking.provider.is_available = True
                # Update Redis presence
                redis_service.set_provider_presence(
                    str(booking.provider.id),
                    ProviderPresenceStatus.ONLINE_AVAILABLE.value
                )
        elif to_status == BookingStatus.CANCELLED:
            booking.cancelled_at = now
            booking.cancellation_reason = reason
            booking.cancelled_by_user_id = changed_by_user.id
            if booking.provider:
                booking.provider.is_available = True
                redis_service.set_provider_presence(
                    str(booking.provider.id),
                    ProviderPresenceStatus.ONLINE_AVAILABLE.value
                )

        history = BookingStatusHistory(
            booking_id=booking.id,
            from_status=from_status,
            to_status=to_status,
            changed_by_user_id=changed_by_user.id,
            reason=reason,
            metadata_json=metadata or {}
        )
        db.add(history)
        db.commit()
        db.refresh(booking)
        return booking

    @classmethod
    def assign_provider(
        cls,
        db: Session,
        booking: Booking,
        provider: ProviderProfile,
        assigned_by: User
    ) -> Booking:
        """
        Concurrency-safe provider assignment:
        Uses SELECT FOR UPDATE on the booking row and ensures only ONE provider
        can transition the booking from REQUESTED/SEARCHING to ASSIGNED.
        Supported by PostgreSQL partial unique index on (booking_id) WHERE status='ACCEPTED'.
        """
        # Re-fetch booking with row lock inside transaction
        locked_booking = (
            db.query(Booking)
            .filter(Booking.id == booking.id)
            .with_for_update()
            .first()
        )

        if not locked_booking:
            raise NotFoundException("Booking not found")

        # Check if booking was already claimed or cancelled
        if locked_booking.status not in [BookingStatus.REQUESTED, BookingStatus.SEARCHING]:
            raise ConflictException(
                f"Booking is already {locked_booking.status.value.lower()} and no longer available"
            )

        if locked_booking.provider_id is not None:
            raise ConflictException("Booking has already been assigned to another provider")

        # Provider check
        if not provider.user.is_active or provider.user.is_suspended:
            raise ForbiddenException("Provider account is inactive or suspended")
        if provider.verification_status.value != "VERIFIED":
            raise ForbiddenException("Provider is not verified")

        offered = db.query(BookingAssignment).filter(
            BookingAssignment.booking_id == locked_booking.id,
            BookingAssignment.provider_id == provider.id,
            BookingAssignment.status == AssignmentStatus.OFFERED,
        ).first()
        if not offered:
            raise ForbiddenException("No active dispatch offer exists for this provider")

        # Check if an assignment record already exists for this provider
        assignment = (
            db.query(BookingAssignment)
            .filter(
                BookingAssignment.booking_id == locked_booking.id,
                BookingAssignment.provider_id == provider.id
            )
            .with_for_update()
            .first()
        )

        from_status = locked_booking.status

        try:
            assignment.status = AssignmentStatus.ACCEPTED

            # Assign provider to booking
            locked_booking.provider_id = provider.id
            locked_booking.provider_snapshot = {
                "provider_id": str(provider.id),
                "user_id": str(provider.user_id),
                "business_name": provider.business_name,
                "rating_average": provider.rating_average,
                "rating_count": provider.rating_count,
            }
            locked_booking.status = BookingStatus.ASSIGNED

            # Provider availability update
            provider.is_available = False

            # Add status history
            history = BookingStatusHistory(
                booking_id=locked_booking.id,
                from_status=from_status,
                to_status=BookingStatus.ASSIGNED,
                changed_by_user_id=assigned_by.id,
                reason=f"Assigned to provider {provider.id}",
                metadata_json={"provider_id": str(provider.id)}
            )
            db.add(history)

            # Commit transaction atomically
            db.commit()
            db.refresh(locked_booking)

            # Update Redis presence to ONLINE_BUSY
            redis_service.set_provider_presence(
                str(provider.id),
                ProviderPresenceStatus.ONLINE_BUSY.value
            )

            return locked_booking

        except IntegrityError as e:
            db.rollback()
            raise ConflictException("Booking was claimed by another provider concurrently")
