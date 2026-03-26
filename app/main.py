import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

app = FastAPI(title="Payments Webhook Service")


class PaymentEvent(BaseModel):
    transaction_id: str
    amount: float
    currency: str = Field(..., min_length=3, max_length=3)
    event_type: str


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def dispatch_payment_event(payload: PaymentEvent) -> dict:
    """Forward a validated payment event to the downstream processor.

    Decorated with tenacity retry: up to 3 attempts, with exponential back-off
    between attempts (1 s before the 2nd attempt, 2 s before the 3rd attempt),
    capped at 10 s, so transient downstream errors are handled automatically.
    """
    # Replace with a real downstream call (e.g. requests.post / httpx) as needed.
    return {"status": "ack", "transaction_id": payload.transaction_id}


@app.post("/webhook/payments")
async def receive_payment(
    payload: PaymentEvent,
    x_webhook_token: str | None = Header(default=None),
) -> dict:
    expected = os.getenv("PAYMENTS_WEBHOOK_TOKEN")
    if not expected or x_webhook_token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return dispatch_payment_event(payload)
