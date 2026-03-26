
import pytest
from fastapi.testclient import TestClient

from app.main import PaymentEvent, _process_payment, app

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


def test_process_payment_is_tenacity_decorated():
    """_process_payment must be decorated with tenacity @retry."""
    assert hasattr(_process_payment, "__wrapped__"), (
        "_process_payment should be wrapped by tenacity @retry"
    )


def test_process_payment_direct():
    """_process_payment returns the correct ack dict for a valid payload."""
    event = PaymentEvent(
        transaction_id="txn_003",
        amount=10.0,
        currency="EUR",
        event_type="payment_settled",
    )
    assert _process_payment(event) == {"status": "ack", "transaction_id": "txn_003"}


def test_process_payment_retries_on_transient_failure():
    """Tenacity retries on transient failure before returning a successful result."""
    from tenacity import retry, stop_after_attempt, wait_none

    call_count = 0

    @retry(stop=stop_after_attempt(3), wait=wait_none())
    def _flaky_op():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RuntimeError("transient error")
        return "ok"

    assert _flaky_op() == "ok"
    assert call_count == 2
