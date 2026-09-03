from fastapi import status


def _setup_completed_booking(client, customer, provider, service):
    # Setup Address & Quote
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
        headers=customer["headers"]
    )
    address_id = addr_res.json()["id"]

    quote_res = client.post(
        "/api/v1/pricing/quote",
        json={"service_id": str(service.id), "is_emergency": False},
        headers=customer["headers"]
    )
    quote_id = quote_res.json()["id"]

    # Book
    booking_res = client.post(
        "/api/v1/bookings",
        json={
            "service_id": str(service.id),
            "quote_id": quote_id,
            "address_id": address_id
        },
        headers=customer["headers"]
    )
    booking_id = booking_res.json()["id"]

    # Assign & Progress
    client.post(f"/api/v1/bookings/{booking_id}/accept", headers=provider["headers"])
    client.post(f"/api/v1/bookings/{booking_id}/status", json={"to_status": "PROVIDER_EN_ROUTE"}, headers=provider["headers"])
    client.post(f"/api/v1/bookings/{booking_id}/status", json={"to_status": "ARRIVED"}, headers=provider["headers"])
    client.post(f"/api/v1/bookings/{booking_id}/status", json={"to_status": "IN_PROGRESS"}, headers=provider["headers"])
    client.post(f"/api/v1/bookings/{booking_id}/status", json={"to_status": "COMPLETED"}, headers=provider["headers"])

    return booking_id


def test_payment_and_earning_flow(client, test_customer, test_provider, test_sample_service):
    booking_id = _setup_completed_booking(client, test_customer, test_provider, test_sample_service)

    # 1. Customer initiates Cash payment
    pay_res = client.post(
        "/api/v1/payments",
        json={"booking_id": booking_id, "payment_method": "CASH"},
        headers=test_customer["headers"]
    )
    assert pay_res.status_code == status.HTTP_201_CREATED
    payment = pay_res.json()
    assert payment["status"] == "PENDING"
    assert payment["payment_method"] == "CASH"
    assert payment["amount"] == 241.5
    payment_id = payment["id"]

    # 2. Provider marks cash payment collected
    complete_res = client.post(
        f"/api/v1/payments/{payment_id}/complete",
        json={},
        headers=test_provider["headers"]
    )
    assert complete_res.status_code == status.HTTP_200_OK
    assert complete_res.json()["status"] == "PAID"

    # 3. Verify Provider Earning was automatically created
    # Amount = 241.5, Commission (15%) = 36.23, Provider Net = 205.27
    booking_detail = client.get(f"/api/v1/bookings/{booking_id}", headers=test_customer["headers"]).json()
    earning = booking_detail["earning"]
    assert earning is not None
    assert earning["gross_amount"] == 241.5
    assert earning["platform_commission"] == 36.23
    assert earning["provider_earning"] == 205.27
    assert earning["payout_status"] == "PENDING"


def test_submit_rating_after_completion(client, test_customer, test_provider, test_sample_service):
    booking_id = _setup_completed_booking(client, test_customer, test_provider, test_sample_service)

    # Customer rates provider 5 stars
    rating_payload = {
        "booking_id": booking_id,
        "score": 5,
        "review_text": "Arrived promptly and fixed the tap leak with no hassle!"
    }
    rating_res = client.post("/api/v1/ratings", json=rating_payload, headers=test_customer["headers"])
    assert rating_res.status_code == status.HTTP_201_CREATED
    rating_data = rating_res.json()
    assert rating_data["score"] == 5

    # Cannot rate twice for same booking
    dup_rating = client.post("/api/v1/ratings", json=rating_payload, headers=test_customer["headers"])
    assert dup_rating.status_code == status.HTTP_409_CONFLICT
