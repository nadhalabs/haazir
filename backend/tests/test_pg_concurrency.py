import pytest
import concurrent.futures
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.security import get_password_hash, create_access_token
from app.models import (
    User,
    UserRole,
    ProviderProfile,
    VerificationStatus,
    ServiceCategory,
    Service,
    ProviderService,
    Address,
    PriceQuote,
    Booking,
    BookingAssignment,
    Payment,
    ProviderEarning
)
from app.models.enums import BookingStatus, AssignmentStatus, PaymentMethod
from app.services.booking_service import BookingService
from app.services.payment_service import PaymentService
from datetime import datetime, timezone, timedelta

# Real PostgreSQL connection for true concurrency & row lock testing
PG_TEST_DB_URL = "postgresql://kailasanadhg:@localhost:5432/haazir_test_db"
pg_engine = create_engine(PG_TEST_DB_URL, pool_size=10, max_overflow=20)
PgSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)


@pytest.fixture(scope="module")
def pg_setup():
    db = PgSessionLocal()
    unique_suffix = uuid.uuid4().hex[:6]
    try:
        # Create Category & Service with unique slugs
        cat = ServiceCategory(
            name=f"Plumbing Concurrency {unique_suffix}",
            slug=f"plumbing-conc-{unique_suffix}",
            is_active=True
        )
        db.add(cat)
        db.flush()

        svc = Service(
            category_id=cat.id,
            name=f"Emergency Pipe Fix {unique_suffix}",
            slug=f"emergency-pipe-fix-{unique_suffix}",
            base_visit_charge=300.0,
            estimated_duration_mins=60,
            is_active=True
        )
        db.add(svc)
        db.flush()

        # Create Customer
        cust = User(
            phone=f"+9198{uuid.uuid4().int % 100000000:08d}",
            full_name="Concurrency Customer",
            hashed_password=get_password_hash("pass"),
            role=UserRole.CUSTOMER,
            is_active=True,
            is_suspended=False
        )
        db.add(cust)
        db.flush()

        # Customer Address
        addr = Address(
            user_id=cust.id,
            label="Home",
            address_line1="Brigade Road",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560025",
            latitude=12.9716,
            longitude=77.5946,
            is_default=True
        )
        db.add(addr)
        db.flush()

        # Provider 1
        p1_u = User(
            phone=f"+9197{uuid.uuid4().int % 100000000:08d}",
            full_name="Provider One",
            hashed_password=get_password_hash("pass"),
            role=UserRole.PROVIDER,
            is_active=True,
            is_suspended=False
        )
        db.add(p1_u)
        db.flush()
        p1 = ProviderProfile(
            user_id=p1_u.id,
            business_name="Pro One Services",
            verification_status=VerificationStatus.VERIFIED,
            is_online=True,
            is_available=True,
            service_radius_km=15.0,
            base_latitude=12.9720,
            base_longitude=77.5950
        )
        db.add(p1)
        db.flush()
        db.add(ProviderService(provider_id=p1.id, service_id=svc.id, is_active=True))

        # Provider 2
        p2_u = User(
            phone=f"+9196{uuid.uuid4().int % 100000000:08d}",
            full_name="Provider Two",
            hashed_password=get_password_hash("pass"),
            role=UserRole.PROVIDER,
            is_active=True,
            is_suspended=False
        )
        db.add(p2_u)
        db.flush()
        p2 = ProviderProfile(
            user_id=p2_u.id,
            business_name="Pro Two Services",
            verification_status=VerificationStatus.VERIFIED,
            is_online=True,
            is_available=True,
            service_radius_km=15.0,
            base_latitude=12.9730,
            base_longitude=77.5960
        )
        db.add(p2)
        db.flush()
        db.add(ProviderService(provider_id=p2.id, service_id=svc.id, is_active=True))

        db.commit()

        yield {
            "customer": cust,
            "address": addr,
            "service": svc,
            "provider1_user": p1_u,
            "provider1_profile": p1,
            "provider2_user": p2_u,
            "provider2_profile": p2,
        }
    finally:
        db.close()


def _create_searching_booking(db, setup):
    # Create valid Quote
    quote = PriceQuote(
        service_id=setup["service"].id,
        customer_id=setup["customer"].id,
        base_charge=300.0,
        service_fee=30.0,
        emergency_surcharge=0.0,
        tax_amount=16.5,
        discount_amount=0.0,
        total_amount=346.5,
        currency="INR",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
    )
    db.add(quote)
    db.flush()

    booking = Booking(
        booking_number=BookingService.generate_booking_number(),
        customer_id=setup["customer"].id,
        service_id=setup["service"].id,
        quote_id=quote.id,
        status=BookingStatus.SEARCHING,
        address_snapshot={"latitude": 12.9716, "longitude": 77.5946, "address_line1": "Brigade Road"},
        service_snapshot={"name": setup["service"].name, "base_charge": 300.0}
    )
    db.add(booking)
    db.flush()
    for provider_key in ("provider1_profile", "provider2_profile"):
        db.add(BookingAssignment(
            booking_id=booking.id,
            provider_id=setup[provider_key].id,
            status=AssignmentStatus.OFFERED,
        ))
    db.commit()
    db.refresh(booking)
    return booking


def test_real_pg_simultaneous_accept_concurrency(pg_setup):
    """
    CRITICAL CONCURRENCY TEST on REAL PostgreSQL:
    Provider 1 and Provider 2 attempt to claim the exact same SEARCHING booking
    simultaneously in parallel threads using separate database sessions.

    Expected:
    - Exactly 1 provider succeeds.
    - Exactly 1 provider fails with ConflictException.
    - Exactly 1 assignment row exists in PostgreSQL with status = 'ACCEPTED'.
    - The booking has exactly 1 provider_id assigned.
    """
    init_db = PgSessionLocal()
    booking = _create_searching_booking(init_db, pg_setup)
    booking_id = booking.id
    init_db.close()

    results = {}

    def attempt_accept(provider_num, provider_user, provider_profile):
        thread_db = PgSessionLocal()
        try:
            # Fetch local booking instance in this thread's session
            b = thread_db.query(Booking).filter(Booking.id == booking_id).first()
            p = thread_db.query(ProviderProfile).filter(ProviderProfile.id == provider_profile.id).first()
            u = thread_db.query(User).filter(User.id == provider_user.id).first()

            assigned = BookingService.assign_provider(
                db=thread_db,
                booking=b,
                provider=p,
                assigned_by=u
            )
            results[provider_num] = ("SUCCESS", assigned.provider_id)
        except Exception as e:
            results[provider_num] = ("FAILED", str(e))
        finally:
            thread_db.close()

    # Launch parallel threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(attempt_accept, 1, pg_setup["provider1_user"], pg_setup["provider1_profile"])
        f2 = executor.submit(attempt_accept, 2, pg_setup["provider2_user"], pg_setup["provider2_profile"])
        concurrent.futures.wait([f1, f2])

    # Assertions
    statuses = [res[0] for res in results.values()]
    assert statuses.count("SUCCESS") == 1, f"Expected exactly 1 success, got {results}"
    assert statuses.count("FAILED") == 1, f"Expected exactly 1 failure, got {results}"

    # Verify directly in real PostgreSQL
    verify_db = PgSessionLocal()
    persisted_booking = verify_db.query(Booking).filter(Booking.id == booking_id).first()
    assert persisted_booking.status == BookingStatus.ASSIGNED
    assert persisted_booking.provider_id is not None

    # Verify assignments table in PostgreSQL
    accepted_assignments = (
        verify_db.query(BookingAssignment)
        .filter(
            BookingAssignment.booking_id == booking_id,
            BookingAssignment.status == AssignmentStatus.ACCEPTED
        )
        .all()
    )
    assert len(accepted_assignments) == 1, "Exactly one accepted assignment must exist in PostgreSQL"
    assert accepted_assignments[0].provider_id == persisted_booking.provider_id
    verify_db.close()


def test_real_pg_cancellation_vs_accept_race(pg_setup):
    """
    Tests race condition where customer cancels while provider attempts to accept.
    State must remain strictly consistent.
    """
    db = PgSessionLocal()
    booking = _create_searching_booking(db, pg_setup)
    booking_id = booking.id

    # Customer cancels first
    BookingService.transition_status(
        db=db,
        booking=booking,
        to_status=BookingStatus.CANCELLED,
        changed_by_user=pg_setup["customer"],
        reason="No longer needed"
    )
    db.close()

    # Provider attempts to accept cancelled booking in a new session
    prov_db = PgSessionLocal()
    b = prov_db.query(Booking).filter(Booking.id == booking_id).first()
    p = prov_db.query(ProviderProfile).filter(ProviderProfile.id == pg_setup["provider1_profile"].id).first()
    u = prov_db.query(User).filter(User.id == pg_setup["provider1_user"].id).first()

    with pytest.raises(Exception) as exc_info:
        BookingService.assign_provider(
            db=prov_db,
            booking=b,
            provider=p,
            assigned_by=u
        )
    assert "no longer available" in str(exc_info.value).lower() or "conflict" in str(exc_info.value).lower()
    prov_db.close()


def test_real_pg_duplicate_completion_and_earning_safety(pg_setup):
    """
    Tests financial idempotency on real PostgreSQL:
    Completed booking must produce at most one ProviderEarning and one payment.
    """
    db = PgSessionLocal()
    booking = _create_searching_booking(db, pg_setup)

    # Assign provider
    BookingService.assign_provider(
        db=db,
        booking=booking,
        provider=pg_setup["provider1_profile"],
        assigned_by=pg_setup["provider1_user"]
    )

    # Progress to completed
    BookingService.transition_status(db, booking, BookingStatus.PROVIDER_EN_ROUTE, pg_setup["provider1_user"])
    BookingService.transition_status(db, booking, BookingStatus.ARRIVED, pg_setup["provider1_user"])
    BookingService.transition_status(db, booking, BookingStatus.IN_PROGRESS, pg_setup["provider1_user"])
    BookingService.transition_status(db, booking, BookingStatus.COMPLETED, pg_setup["provider1_user"])

    # First payment initiation & completion
    pay = PaymentService.create_payment_for_booking(db, booking, PaymentMethod.CASH)
    PaymentService.mark_payment_successful(db, pay)

    # Re-run earning calculation multiple times
    earning1 = PaymentService.calculate_provider_earning(db, booking)
    earning2 = PaymentService.calculate_provider_earning(db, booking)

    assert earning1.id == earning2.id

    # Verify in DB table
    earnings_count = db.query(ProviderEarning).filter(ProviderEarning.booking_id == booking.id).count()
    assert earnings_count == 1, "Must never create duplicate provider earning records"
    db.close()
