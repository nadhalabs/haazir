import pytest
import uuid
from fastapi import status
from app.core.redis import redis_service, DEFAULT_PROVIDER_TTL_SECONDS
from app.models.enums import (
    UserRole,
    VerificationStatus,
    ProviderPresenceStatus,
    BookingStatus,
    AssignmentStatus
)
from app.models import (
    User,
    ProviderProfile,
    ServiceCategory,
    Service,
    ProviderService,
    Address,
    Booking,
    BookingAssignment
)
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
def clean_redis():
    if redis_service.client:
        redis_service.client.flushdb()
    yield
    if redis_service.client:
        redis_service.client.flushdb()


def test_provider_location_heartbeat_and_redis_ttl(client, test_provider, clean_redis):
    # Provider sends live location heartbeat
    payload = {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "presence_status": "ONLINE_AVAILABLE"
    }
    res = client.post("/api/v1/providers/me/location", json=payload, headers=test_provider["headers"])
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "updated"

    # Verify directly in Redis
    provider_id_str = str(test_provider["profile"].id)
    presence = redis_service.get_provider_presence(provider_id_str)
    assert presence is not None
    assert presence["presence_status"] == "ONLINE_AVAILABLE"
    assert round(presence["latitude"], 4) == 12.9716
    assert round(presence["longitude"], 4) == 77.5946

    # Verify TTL is set (> 200s and <= 300s)
    if redis_service.client:
        ttl = redis_service.client.ttl(f"haazir:provider:presence:{provider_id_str}")
        assert ttl > 0 and ttl <= DEFAULT_PROVIDER_TTL_SECONDS


def test_invalid_coordinates_rejected(client, test_provider):
    payload = {
        "latitude": 95.0,  # Invalid latitude (> 90)
        "longitude": 77.5946,
        "presence_status": "ONLINE_AVAILABLE"
    }
    res = client.post("/api/v1/providers/me/location", json=payload, headers=test_provider["headers"])
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_dispatch_eligibility_and_filters(client, db_session, test_customer, clean_redis):
    # 1. Create a service
    cat = ServiceCategory(name="Electrical", slug="electrical", is_active=True)
    db_session.add(cat)
    db_session.flush()

    service = Service(
        category_id=cat.id,
        name="Switchboard Repair",
        slug="switchboard-repair",
        base_visit_charge=150.0,
        estimated_duration_mins=30,
        is_active=True
    )
    db_session.add(service)
    db_session.flush()

    # Create Customer Address
    cust_addr = Address(
        user_id=test_customer["user"].id,
        label="Home",
        address_line1="MG Road",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560001",
        latitude=12.9716,
        longitude=77.5946,
        is_default=True
    )
    db_session.add(cust_addr)
    db_session.flush()

    # Helper to create a provider
    def _create_provider(name, phone, verified, suspended, offers_service, online_db, presence, lat, lon, radius):
        u = User(
            phone=phone,
            full_name=name,
            hashed_password=get_password_hash("pass"),
            role=UserRole.PROVIDER,
            is_active=True,
            is_suspended=suspended
        )
        db_session.add(u)
        db_session.flush()
        p = ProviderProfile(
            user_id=u.id,
            verification_status=VerificationStatus.VERIFIED if verified else VerificationStatus.PENDING,
            is_online=online_db,
            is_available=True,
            service_radius_km=radius,
            base_latitude=lat,
            base_longitude=lon,
            rating_average=4.8
        )
        db_session.add(p)
        db_session.flush()

        if offers_service:
            ps = ProviderService(provider_id=p.id, service_id=service.id, is_active=True)
            db_session.add(ps)
            db_session.flush()

        if presence:
            redis_service.update_provider_location(
                provider_id=str(p.id),
                latitude=lat,
                longitude=lon,
                presence_status=presence,
                service_radius_km=radius
            )
        return p

    # P1: Eligible, verified, online_available, 2km away
    p_eligible = _create_provider("P1 Eligible", "+919111111101", verified=True, suspended=False, offers_service=True, online_db=True, presence="ONLINE_AVAILABLE", lat=12.9750, lon=77.5980, radius=10.0)
    # P2: Unverified
    p_unverified = _create_provider("P2 Unverified", "+919111111102", verified=False, suspended=False, offers_service=True, online_db=True, presence="ONLINE_AVAILABLE", lat=12.9750, lon=77.5980, radius=10.0)
    # P3: Suspended
    p_suspended = _create_provider("P3 Suspended", "+919111111103", verified=True, suspended=True, offers_service=True, online_db=True, presence="ONLINE_AVAILABLE", lat=12.9750, lon=77.5980, radius=10.0)
    # P4: Busy
    p_busy = _create_provider("P4 Busy", "+919111111104", verified=True, suspended=False, offers_service=True, online_db=True, presence="ONLINE_BUSY", lat=12.9750, lon=77.5980, radius=10.0)
    # P5: Offline / Missing from Redis
    p_offline = _create_provider("P5 Offline", "+919111111105", verified=True, suspended=False, offers_service=True, online_db=True, presence="OFFLINE", lat=12.9750, lon=77.5980, radius=10.0)
    # P6: Does NOT offer service
    p_no_service = _create_provider("P6 No Service", "+919111111106", verified=True, suspended=False, offers_service=False, online_db=True, presence="ONLINE_AVAILABLE", lat=12.9750, lon=77.5980, radius=10.0)
    # P7: Outside service radius (50km away with 10km radius)
    p_outside = _create_provider("P7 Outside Radius", "+919111111107", verified=True, suspended=False, offers_service=True, online_db=True, presence="ONLINE_AVAILABLE", lat=13.5000, lon=78.0000, radius=10.0)

    db_session.commit()

    # Query dispatch service
    from app.services.dispatch_service import DispatchService
    results = DispatchService.find_eligible_providers(
        db=db_session,
        service_id=service.id,
        latitude=12.9716,
        longitude=77.5946
    )

    found_ids = [str(item[0].id) for item in results]
    assert str(p_eligible.id) in found_ids
    assert str(p_unverified.id) not in found_ids
    assert str(p_suspended.id) not in found_ids
    assert str(p_busy.id) not in found_ids
    assert str(p_offline.id) not in found_ids
    assert str(p_no_service.id) not in found_ids
    assert str(p_outside.id) not in found_ids


def test_provider_reject_offer(client, db_session, test_customer, test_provider, test_sample_service):
    # Customer books
    addr_res = client.post("/api/v1/users/addresses", json={
        "label": "Home", "address_line1": "100 MG Road", "city": "Bengaluru",
        "state": "Karnataka", "postal_code": "560001", "latitude": 12.9716, "longitude": 77.5946
    }, headers=test_customer["headers"])
    address_id = addr_res.json()["id"]

    quote_res = client.post("/api/v1/pricing/quote", json={"service_id": str(test_sample_service.id)}, headers=test_customer["headers"])
    quote_id = quote_res.json()["id"]

    booking_res = client.post("/api/v1/bookings", json={
        "service_id": str(test_sample_service.id), "quote_id": quote_id, "address_id": address_id
    }, headers=test_customer["headers"])
    booking_id = booking_res.json()["id"]

    # Dispatch: transitions to SEARCHING and creates OFFERED assignment
    dispatch_res = client.post(f"/api/v1/bookings/{booking_id}/dispatch", headers=test_customer["headers"])
    assert dispatch_res.status_code == status.HTTP_200_OK

    # Create an offer for test_provider manually if dispatch didn't find geo
    assign = BookingAssignment(
        booking_id=uuid.UUID(booking_id),
        provider_id=test_provider["profile"].id,
        status=AssignmentStatus.OFFERED
    )
    db_session.add(assign)
    db_session.commit()

    # Provider rejects
    reject_res = client.post(f"/api/v1/bookings/{booking_id}/reject", headers=test_provider["headers"])
    assert reject_res.status_code == status.HTTP_200_OK
    assert reject_res.json()["status"] == "rejected"

    # Verify DB assignment is REJECTED
    db_session.refresh(assign)
    assert assign.status == AssignmentStatus.REJECTED
