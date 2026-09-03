from fastapi import status
from starlette.websockets import WebSocketDisconnect
import pytest


def test_customer_cannot_access_admin_endpoints(client, test_customer):
    res = client.get("/api/v1/admin/users", headers=test_customer["headers"])
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_provider_cannot_access_admin_endpoints(client, test_provider):
    res = client.get("/api/v1/admin/users", headers=test_provider["headers"])
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_access_admin_endpoints(client, test_admin):
    res = client.get("/api/v1/admin/users", headers=test_admin["headers"])
    assert res.status_code == status.HTTP_200_OK
    assert isinstance(res.json(), list)


def test_provider_websocket_rejects_missing_or_wrong_identity(client, test_customer, test_provider):
    provider_id = test_provider["profile"].id
    with pytest.raises(WebSocketDisconnect) as missing:
        with client.websocket_connect(f"/api/v1/ws/providers/{provider_id}"):
            pass
    assert missing.value.code == 1008

    with pytest.raises(WebSocketDisconnect) as wrong_user:
        with client.websocket_connect(
            f"/api/v1/ws/providers/{provider_id}?token={test_customer['token']}"
        ):
            pass
    assert wrong_user.value.code == 1008

    with client.websocket_connect(
        f"/api/v1/ws/providers/{provider_id}?token={test_provider['token']}"
    ) as websocket:
        websocket.send_text("ping")
        assert websocket.receive_json()["event"] == "pong"


def test_idor_address_protection(client, test_customer, test_customer_2):
    # Customer 1 creates an address
    addr_data = {
        "label": "Home",
        "address_line1": "Flat 101, Palm Grove",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560001",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "is_default": True
    }
    create_res = client.post("/api/v1/users/addresses", json=addr_data, headers=test_customer["headers"])
    assert create_res.status_code == status.HTTP_201_CREATED
    address_id = create_res.json()["id"]

    # Customer 2 attempts to modify Customer 1's address (IDOR attempt)
    tamper_res = client.put(
        f"/api/v1/users/addresses/{address_id}",
        json={"city": "Hacked City"},
        headers=test_customer_2["headers"]
    )
    assert tamper_res.status_code == status.HTTP_403_FORBIDDEN

    # Customer 2 attempts to delete Customer 1's address
    delete_res = client.delete(f"/api/v1/users/addresses/{address_id}", headers=test_customer_2["headers"])
    assert delete_res.status_code == status.HTTP_403_FORBIDDEN
