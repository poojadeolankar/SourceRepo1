import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from retrying import retry

app = FastAPI(title="Payments Webhook Service")


class PaymentEvent(BaseModel):
    transaction_id: str
    amount: float
    currency: str = Field(..., min_length=3, max_length=3)
    event_type: str


def _is_transient_error(exception: BaseException) -> bool:
    return isinstance(exception, (IOError, ConnectionError))


def _execute_payment(payload: PaymentEvent) -> dict:
    return {"status": "ack", "transaction_id": payload.transaction_id}


@retry(
    stop_max_attempt_number=3,
    wait_fixed=100,
    retry_on_exception=_is_transient_error,
)
def process_payment(payload: PaymentEvent) -> dict:
    return _execute_payment(payload)


@app.post("/webhook/payments")
async def receive_payment(
    payload: PaymentEvent,
    x_webhook_token: str | None = Header(default=None),
) -> dict:
    expected = os.getenv("PAYMENTS_WEBHOOK_TOKEN")
    if not expected or x_webhook_token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return process_payment(payload)
