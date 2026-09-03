from fastapi import status
from app.models.enums import UserRole


def test_customer_registration_and_login(client):
    reg_data = {
        "phone": "+919876543210",
        "password": "StrongPassword123!",
        "full_name": "Ravi Kumar",
        "email": "ravi@example.com",
        "role": "CUSTOMER"
    }
    # Register
    res = client.post("/api/v1/auth/register", json=reg_data)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["phone"] == reg_data["phone"]
    assert data["role"] == "CUSTOMER"

    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "phone": reg_data["phone"],
        "password": reg_data["password"]
    })
    assert login_res.status_code == status.HTTP_200_OK
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # Test /me with access token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me_res.status_code == status.HTTP_200_OK
    assert me_res.json()["phone"] == reg_data["phone"]


def test_cannot_self_register_admin(client):
    reg_data = {
        "phone": "+919876543211",
        "password": "StrongPassword123!",
        "full_name": "Fake Admin",
        "role": "ADMIN"
    }
    res = client.post("/api/v1/auth/register", json=reg_data)
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_suspended_account_cannot_login(client, db_session, test_customer):
    # Suspend customer
    user = test_customer["user"]
    user.is_suspended = True
    db_session.commit()

    res = client.post("/api/v1/auth/login", json={
        "phone": user.phone,
        "password": "password123"
    })
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "suspended" in res.json()["detail"].lower()


def test_suspended_account_token_rejected(client, db_session, test_customer):
    headers = test_customer["headers"]
    user = test_customer["user"]

    # Verify works initially
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    # Suspend user
    user.is_suspended = True
    db_session.commit()

    # Verify immediately blocked
    res2 = client.get("/api/v1/auth/me", headers=headers)
    assert res2.status_code == status.HTTP_403_FORBIDDEN
    assert "suspended" in res2.json()["detail"].lower()
