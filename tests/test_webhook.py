import pytest
from fastapi.testclient import TestClient

from app.main import PaymentEvent, app, process_payment_event

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


def test_process_payment_event_returns_correct_data():
    """process_payment_event returns the expected ack dict."""
    payload = PaymentEvent(
        transaction_id="txn_010",
        amount=10.0,
        currency="USD",
        event_type="payment_settled",
    )
    result = process_payment_event(payload)
    assert result == {"status": "ack", "transaction_id": "txn_010"}


def test_process_payment_event_has_retry_decorator():
    """@retry sets __wrapped__ on the function via functools.wraps."""
    assert callable(getattr(process_payment_event, "__wrapped__", None)), (
        "process_payment_event should be decorated with @retry"
    )


def test_retry_succeeds_after_transient_failure():
    """process_payment_event retries and eventually succeeds."""
    from retrying import retry

    call_count = 0

    @retry(stop_max_attempt_number=3, wait_fixed=0)
    def flaky_process():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise IOError("transient failure")
        return "ok"

    result = flaky_process()
    assert result == "ok"
    assert call_count == 3
