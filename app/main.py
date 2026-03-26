import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Payments Webhook Service")


class PaymentEvent(BaseModel):
    transaction_id: str
    amount: float
    currency: str = Field(..., min_length=3, max_length=3)
    event_type: str


@app.post("/webhook/payments")
async def receive_payment(
    payload: PaymentEvent,
    x_webhook_token: str | None = Header(default=None),
) -> dict:
    expected = os.getenv("PAYMENTS_WEBHOOK_TOKEN")
    if not expected or x_webhook_token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return {"status": "ack", "transaction_id": payload.transaction_id}
