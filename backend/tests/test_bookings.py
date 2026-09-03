from fastapi import status


def _create_address_and_quote(client, customer_headers, service_id):
    # Create Address
    addr_res = client.post(
        "/api/v1/users/addresses",
        json={
            "label": "Home",
            "address_line1": "100 MG Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560001",
            "latitude": 12.9716,
            "longitude": 77.5946
        },
        headers=customer_headers
    )
    address_id = addr_res.json()["id"]

    # Request Quote
    quote_res = client.post(
        "/api/v1/pricing/quote",
        json={"service_id": str(service_id), "is_emergency": False},
        headers=customer_headers
    )
    quote_id = quote_res.json()["id"]

    return address_id, quote_id


def test_booking_creation_and_lifecycle(client, test_customer, test_provider, test_sample_service):
    address_id, quote_id = _create_address_and_quote(client, test_customer["headers"], test_sample_service.id)

    # 1. Customer creates booking
    booking_payload = {
        "service_id": str(test_sample_service.id),
        "quote_id": quote_id,
        "address_id": address_id,
        "customer_notes": "Main tap is leaking badly"
    }
    booking_res = client.post("/api/v1/bookings", json=booking_payload, headers=test_customer["headers"])
    assert booking_res.status_code == status.HTTP_201_CREATED
    booking = booking_res.json()
    assert booking["status"] == "REQUESTED"
    assert booking["address_snapshot"]["address_line1"] == "100 MG Road"
    booking_id = booking["id"]

    # 2. Cannot reuse same quote
    dup_res = client.post("/api/v1/bookings", json=booking_payload, headers=test_customer["headers"])
    assert dup_res.status_code == status.HTTP_400_BAD_REQUEST

    # 3. Provider accepts the booking
    accept_res = client.post(f"/api/v1/bookings/{booking_id}/accept", headers=test_provider["headers"])
    assert accept_res.status_code == status.HTTP_200_OK
    assert accept_res.json()["status"] == "ASSIGNED"
    assert accept_res.json()["provider_id"] == str(test_provider["profile"].id)

    # 4. Provider transitions: ASSIGNED -> PROVIDER_EN_ROUTE
    en_route_res = client.post(
        f"/api/v1/bookings/{booking_id}/status",
        json={"to_status": "PROVIDER_EN_ROUTE"},
        headers=test_provider["headers"]
    )
    assert en_route_res.status_code == status.HTTP_200_OK
    assert en_route_res.json()["status"] == "PROVIDER_EN_ROUTE"

    # 5. Invalid transition attempt (PROVIDER_EN_ROUTE cannot jump directly to COMPLETED)
    invalid_res = client.post(
        f"/api/v1/bookings/{booking_id}/status",
        json={"to_status": "COMPLETED"},
        headers=test_provider["headers"]
    )
    assert invalid_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Illegal state transition" in invalid_res.json()["detail"]

    # 6. Valid transitions to ARRIVED -> IN_PROGRESS -> COMPLETED
    arrived_res = client.post(
        f"/api/v1/bookings/{booking_id}/status",
        json={"to_status": "ARRIVED"},
        headers=test_provider["headers"]
    )
    assert arrived_res.status_code == status.HTTP_200_OK

    started_res = client.post(
        f"/api/v1/bookings/{booking_id}/status",
        json={"to_status": "IN_PROGRESS"},
        headers=test_provider["headers"]
    )
    assert started_res.status_code == status.HTTP_200_OK

    completed_res = client.post(
        f"/api/v1/bookings/{booking_id}/status",
        json={"to_status": "COMPLETED"},
        headers=test_provider["headers"]
    )
    assert completed_res.status_code == status.HTTP_200_OK
    assert completed_res.json()["status"] == "COMPLETED"


def test_booking_idor_protection(client, test_customer, test_customer_2, test_sample_service):
    address_id, quote_id = _create_address_and_quote(client, test_customer["headers"], test_sample_service.id)

    booking_payload = {
        "service_id": str(test_sample_service.id),
        "quote_id": quote_id,
        "address_id": address_id
    }
    booking_res = client.post("/api/v1/bookings", json=booking_payload, headers=test_customer["headers"])
    booking_id = booking_res.json()["id"]

    # Customer 2 attempts to view Customer 1's booking
    view_res = client.get(f"/api/v1/bookings/{booking_id}", headers=test_customer_2["headers"])
    assert view_res.status_code == status.HTTP_403_FORBIDDEN

    # Customer 2 attempts to cancel Customer 1's booking
    cancel_res = client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        json={"cancellation_reason": "Malicious cancellation"},
        headers=test_customer_2["headers"]
    )
    assert cancel_res.status_code == status.HTTP_403_FORBIDDEN
