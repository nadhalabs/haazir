import math
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.provider import ProviderProfile, ProviderDocument
from app.models.service import ProviderService, Service
from app.models.booking import Booking, BookingAssignment
from app.models.user import User
from app.models.enums import (
    VerificationStatus,
    ProviderPresenceStatus,
    BookingStatus,
    AssignmentStatus,
    UserRole
)
from app.core.redis import redis_service, DEFAULT_PROVIDER_TTL_SECONDS
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException,
    ForbiddenException
)
from app.services.adapters.routing_adapter import BasicRoutingAdapter
import uuid

logger = logging.getLogger(__name__)


class DispatchService:
    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return BasicRoutingAdapter.calculate_distance_km(lat1, lon1, lat2, lon2)

    @classmethod
    def find_eligible_providers(
        cls,
        db: Session,
        service_id: uuid.UUID,
        latitude: float,
        longitude: float,
        limit: int = 10,
        max_search_radius_km: float = 25.0
    ) -> List[Tuple[ProviderProfile, float, Dict[str, Any]]]:
        """
        Finds eligible providers matching all 8 dispatch conditions:
        1. Offers requested service (ProviderService is_active).
        2. Verified provider (VerificationStatus.VERIFIED).
        3. Active, non-suspended account in PostgreSQL.
        4. Present in Redis with fresh TTL (excludes stale location).
        5. Live presence status == ONLINE_AVAILABLE (not busy / offline).
        6. Within provider's service_radius_km of job location.
        7. Sorted nearest first, then by rating average.
        8. Returns (ProviderProfile, distance_km, eta_info).
        """
        # Step A: Query base candidate providers offering this service from PostgreSQL
        candidates = (
            db.query(ProviderProfile)
            .join(User, User.id == ProviderProfile.user_id)
            .join(ProviderService, ProviderService.provider_id == ProviderProfile.id)
            .filter(
                ProviderService.service_id == service_id,
                ProviderService.is_active == True,
                ProviderProfile.verification_status == VerificationStatus.VERIFIED,
                User.is_active == True,
                User.is_suspended == False
            )
            .all()
        )

        eligible: List[Tuple[ProviderProfile, float, Dict[str, Any]]] = []
        routing_adapter = BasicRoutingAdapter()

        # Step B: Check live presence & location from Redis
        for provider in candidates:
            # First check live Redis presence
            live_presence = redis_service.get_provider_presence(str(provider.id))

            if live_presence:
                # Must be ONLINE_AVAILABLE
                if live_presence.get("presence_status") != ProviderPresenceStatus.ONLINE_AVAILABLE.value:
                    continue

                p_lat = live_presence.get("latitude")
                p_lon = live_presence.get("longitude")
                service_radius = live_presence.get("service_radius_km", provider.service_radius_km)
            else:
                # Live Redis presence is authoritative. During an outage dispatch pauses;
                # durable DB flags/coordinates must never masquerade as fresh presence.
                continue

            # Calculate distance
            dist_km = cls.haversine_distance_km(latitude, longitude, p_lat, p_lon)

            # Check radius compliance
            if dist_km <= service_radius and dist_km <= max_search_radius_km:
                eta = routing_adapter.calculate_eta(p_lat, p_lon, latitude, longitude)
                eligible.append((provider, dist_km, eta))

        # Sort nearest first, then by rating average descending
        eligible.sort(key=lambda x: (x[1], -x[0].rating_average))
        return eligible[:limit]

    @classmethod
    def dispatch_booking(
        cls,
        db: Session,
        booking_id: uuid.UUID,
        max_offers: int = 5
    ) -> List[BookingAssignment]:
        """
        Initiates dispatch workflow for a booking:
        Moves status to SEARCHING, locates eligible providers, creates OFFERED assignments.
        If no eligible providers, transitions booking to FAILED (or maintains SEARCHING with empty offers).
        """
        booking = (
            db.query(Booking)
            .filter(Booking.id == booking_id)
            .with_for_update()
            .first()
        )
        if not booking:
            raise NotFoundException("Booking not found")

        if booking.status not in [BookingStatus.REQUESTED, BookingStatus.SEARCHING]:
            raise BadRequestException(f"Cannot dispatch booking in status {booking.status.value}")

        # Ensure status is SEARCHING
        if booking.status == BookingStatus.REQUESTED:
            from app.services.booking_service import BookingService
            BookingService.transition_status(
                db=db,
                booking=booking,
                to_status=BookingStatus.SEARCHING,
                changed_by_user=booking.customer,
                reason="Searching for nearby service professionals"
            )

        # Retrieve job coordinates from address snapshot
        addr = booking.address_snapshot
        lat = addr.get("latitude")
        lon = addr.get("longitude")

        if lat is None or lon is None:
            raise BadRequestException("Booking address missing latitude/longitude coordinates")

        # Find eligible providers
        eligible = cls.find_eligible_providers(
            db=db,
            service_id=booking.service_id,
            latitude=float(lat),
            longitude=float(lon),
            limit=max_offers
        )

        if not eligible:
            # Mark as FAILED or leave as SEARCHING depending on policy
            return []

        assignments: List[BookingAssignment] = []
        for provider, dist_km, eta in eligible:
            # Check if offer already created for this provider
            existing = (
                db.query(BookingAssignment)
                .filter(
                    BookingAssignment.booking_id == booking.id,
                    BookingAssignment.provider_id == provider.id
                )
                .first()
            )
            if not existing:
                assignment = BookingAssignment(
                    booking_id=booking.id,
                    provider_id=provider.id,
                    status=AssignmentStatus.OFFERED
                )
                db.add(assignment)
                assignments.append(assignment)

        db.commit()
        return assignments

    @classmethod
    def reject_assignment(
        cls,
        db: Session,
        booking_id: uuid.UUID,
        provider_user: User,
        reason: Optional[str] = None
    ) -> BookingAssignment:
        """
        Provider rejects an offer.
        """
        profile = (
            db.query(ProviderProfile)
            .filter(ProviderProfile.user_id == provider_user.id)
            .first()
        )
        if not profile:
            raise ForbiddenException("Provider profile not found")

        assignment = (
            db.query(BookingAssignment)
            .filter(
                BookingAssignment.booking_id == booking_id,
                BookingAssignment.provider_id == profile.id
            )
            .with_for_update()
            .first()
        )
        if not assignment:
            raise NotFoundException("Offer assignment not found for this provider")

        if assignment.status != AssignmentStatus.OFFERED:
            raise BadRequestException(f"Assignment is not in OFFERED state (current: {assignment.status.value})")

        assignment.status = AssignmentStatus.REJECTED
        db.commit()
        db.refresh(assignment)
        return assignment

    @classmethod
    def timeout_assignment(
        cls,
        db: Session,
        assignment_id: uuid.UUID
    ) -> BookingAssignment:
        """
        Marks an unaccepted offer as TIMEOUT.
        """
        assignment = (
            db.query(BookingAssignment)
            .filter(BookingAssignment.id == assignment_id)
            .with_for_update()
            .first()
        )
        if not assignment:
            raise NotFoundException("Assignment not found")

        if assignment.status == AssignmentStatus.OFFERED:
            assignment.status = AssignmentStatus.TIMEOUT
            db.commit()
            db.refresh(assignment)
        return assignment
