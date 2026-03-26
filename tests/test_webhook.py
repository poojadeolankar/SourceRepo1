import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import PaymentEvent, _is_transient, _process_payment, app

TOKEN = "test-secret-token"
VALID_PAYLOAD = {
    "transaction_id": "txn_001",
    "amount": 99.99,
    "currency": "USD",
    "event_type": "payment_settled",
}


@pytest.fixture(autouse=True)
def set_token(monkeypatch):
    monkeypatch.setenv("PAYMENTS_WEBHOOK_TOKEN", TOKEN)


@pytest.fixture
def client():
    return TestClient(app)


def test_valid_payment(client):
    response = client.post(
        "/webhook/payments",
        json=VALID_PAYLOAD,
        headers={"x-webhook-token": TOKEN},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ack", "transaction_id": "txn_001"}


def test_invalid_token(client):
    response = client.post(
        "/webhook/payments",
        json=VALID_PAYLOAD,
        headers={"x-webhook-token": "wrong-token"},
    )
    assert response.status_code == 401


def test_invalid_payload(client):
    # missing required fields: currency, event_type
    response = client.post(
        "/webhook/payments",
        json={"transaction_id": "txn_002", "amount": 50.0},
        headers={"x-webhook-token": TOKEN},
    )
    assert response.status_code == 422


def test_process_payment_retries_on_transient_error():
    payload = PaymentEvent(**VALID_PAYLOAD)

    # Verify _is_transient correctly identifies transient vs non-transient errors
    assert _is_transient(IOError("transient")) is True
    assert _is_transient(ConnectionError("conn")) is True
    assert _is_transient(HTTPException(status_code=400)) is False

    # Verify normal execution still works
    result = _process_payment(payload)
    assert result["status"] == "ack"


def test_process_payment_succeeds_without_error():
    payload = PaymentEvent(**VALID_PAYLOAD)
    result = _process_payment(payload)
    assert result == {"status": "ack", "transaction_id": "txn_001"}


def test_process_payment_does_not_retry_http_exception():
    # HTTPException should NOT be considered transient (no retry)
    assert _is_transient(HTTPException(status_code=500, detail="server error")) is False
    assert _is_transient(HTTPException(status_code=503, detail="unavailable")) is False
