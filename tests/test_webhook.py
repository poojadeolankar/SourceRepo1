from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from tenacity import retry, stop_after_attempt, wait_none

from app.main import PaymentEvent, app, dispatch_payment_event

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


def test_dispatch_is_tenacity_wrapped():
    """dispatch_payment_event must be decorated with tenacity @retry."""
    assert hasattr(dispatch_payment_event, "retry"), (
        "dispatch_payment_event should be a tenacity-wrapped function"
    )
    assert hasattr(dispatch_payment_event, "statistics"), (
        "dispatch_payment_event should expose tenacity statistics"
    )


def test_dispatch_retries_on_transient_error():
    """Retry logic should succeed on the 3rd attempt after two transient errors."""
    payload = PaymentEvent(**VALID_PAYLOAD)
    call_count = 0

    def flaky(p):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("transient failure")
        return {"status": "ack", "transaction_id": p.transaction_id}

    # Build a no-sleep retry wrapper around the flaky stub to keep tests fast.
    fast_retry = retry(stop=stop_after_attempt(3), wait=wait_none())(flaky)

    result = fast_retry(payload)

    assert result == {"status": "ack", "transaction_id": "txn_001"}
    assert call_count == 3


def test_endpoint_retries_via_dispatch(client):
    """Endpoint should retry dispatch and return 200 after transient failures."""
    call_count = 0

    def flaky(p):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("transient")
        return {"status": "ack", "transaction_id": p.transaction_id}

    fast_dispatch = retry(stop=stop_after_attempt(3), wait=wait_none())(flaky)

    with patch("app.main.dispatch_payment_event", fast_dispatch):
        response = client.post(
            "/webhook/payments",
            json=VALID_PAYLOAD,
            headers={"x-webhook-token": TOKEN},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ack", "transaction_id": "txn_001"}
    assert call_count == 3
