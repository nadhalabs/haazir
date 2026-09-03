import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.models import (
    User,
    UserRole,
    Address,
    ProviderProfile,
    VerificationStatus,
    ServiceCategory,
    Service,
    ProviderService
)

# Use in-memory SQLite for high-speed isolated unit testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_admin(db_session):
    user = User(
        phone="+919999900000",
        email="admin@test.com",
        full_name="Test Admin",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_suspended=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def test_customer(db_session):
    user = User(
        phone="+919999900001",
        email="customer1@test.com",
        full_name="Test Customer 1",
        hashed_password=get_password_hash("password123"),
        role=UserRole.CUSTOMER,
        is_active=True,
        is_suspended=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def test_customer_2(db_session):
    user = User(
        phone="+919999900002",
        email="customer2@test.com",
        full_name="Test Customer 2",
        hashed_password=get_password_hash("password123"),
        role=UserRole.CUSTOMER,
        is_active=True,
        is_suspended=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def test_provider(db_session):
    user = User(
        phone="+919999900003",
        email="provider1@test.com",
        full_name="Test Plumber",
        hashed_password=get_password_hash("password123"),
        role=UserRole.PROVIDER,
        is_active=True,
        is_suspended=False
    )
    db_session.add(user)
    db_session.flush()

    profile = ProviderProfile(
        user_id=user.id,
        business_name="Fast Plumbing Services",
        verification_status=VerificationStatus.VERIFIED,
        is_online=True,
        is_available=True,
        service_radius_km=15.0,
        base_latitude=12.9716,
        base_longitude=77.5946
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(profile)

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {
        "user": user,
        "profile": profile,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


@pytest.fixture
def test_sample_service(db_session):
    category = ServiceCategory(
        name="Plumbing",
        slug="plumbing",
        is_active=True
    )
    db_session.add(category)
    db_session.flush()

    service = Service(
        category_id=category.id,
        name="Tap Leak Repair",
        slug="tap-leak-repair",
        base_visit_charge=200.0,
        min_charge=150.0,
        emergency_surcharge_rate=100.0,
        estimated_duration_mins=45,
        is_active=True
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(category)
    db_session.refresh(service)
    return service
