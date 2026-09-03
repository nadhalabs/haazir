from fastapi import status


def test_server_authoritative_quote_calculation(client, test_customer, test_sample_service):
    # Base visit charge is 200, service fee is 30, emergency is False
    # Subtotal = 230, Tax (5%) = 11.5, Total = 241.5
    quote_payload = {
        "service_id": str(test_sample_service.id),
        "is_emergency": False
    }
    res = client.post("/api/v1/pricing/quote", json=quote_payload, headers=test_customer["headers"])
    assert res.status_code == status.HTTP_200_OK
    quote = res.json()
    assert quote["base_charge"] == 200.0
    assert quote["service_fee"] == 30.0
    assert quote["emergency_surcharge"] == 0.0
    assert quote["tax_amount"] == 11.5
    assert quote["total_amount"] == 241.5
    assert "expires_at" in quote


def test_quote_with_emergency_surcharge(client, test_customer, test_sample_service):
    # Base = 200, Service Fee = 30, Emergency = 100
    # Subtotal = 330, Tax (5%) = 16.5, Total = 346.5
    quote_payload = {
        "service_id": str(test_sample_service.id),
        "is_emergency": True
    }
    res = client.post("/api/v1/pricing/quote", json=quote_payload, headers=test_customer["headers"])
    assert res.status_code == status.HTTP_200_OK
    quote = res.json()
    assert quote["emergency_surcharge"] == 100.0
    assert quote["total_amount"] == 346.5
