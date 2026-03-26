import pytest
from fastapi.testclient import TestClient

from app.main import app

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


def test_retry_on_transient_error(client, monkeypatch):
    call_count = 0

    def flaky_execute(payload):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise IOError("transient failure")
        return {"status": "ack", "transaction_id": payload.transaction_id}

    monkeypatch.setattr("app.main._execute_payment", flaky_execute)
    response = client.post(
        "/webhook/payments",
        json=VALID_PAYLOAD,
        headers={"x-webhook-token": TOKEN},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ack", "transaction_id": "txn_001"}
    assert call_count == 3


def test_no_retry_on_non_transient_error(client, monkeypatch):
    call_count = 0

    def non_transient_fail(payload):
        nonlocal call_count
        call_count += 1
        raise ValueError("non-transient failure")

    monkeypatch.setattr("app.main._execute_payment", non_transient_fail)
    with pytest.raises(ValueError, match="non-transient failure"):
        client.post(
            "/webhook/payments",
            json=VALID_PAYLOAD,
            headers={"x-webhook-token": TOKEN},
        )
    assert call_count == 1
