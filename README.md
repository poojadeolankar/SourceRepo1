# Payments Webhook Service

A minimal, production-ready **FastAPI** service that receives and validates inbound bank payment webhook events. Built with security-first design: every request is authenticated via a bearer token read from an environment variable — no secrets are ever hard-coded.

---

## What It Does

- Exposes a single `POST /webhook/payments` HTTP endpoint.
- Validates the incoming JSON payload against a strict `PaymentEvent` schema (Pydantic v2).
- Authenticates every request using the `X-Webhook-Token` header, compared against the `PAYMENTS_WEBHOOK_TOKEN` environment variable.
- Returns a JSON acknowledgement `{"status": "ack", "transaction_id": "<id>"}` on success.
- Returns `401 Unauthorized` if the token is missing or wrong.
- Returns `422 Unprocessable Entity` if the payload does not match the required schema.

---

## Project Structure

```
SourceRepo1/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app & webhook endpoint
│   └── example_env.py    # Reference only — shows correct secret handling pattern
├── tests/
│   ├── __init__.py
│   └── test_webhook.py   # 3 pytest test cases covering all response paths
├── .github/
│   └── workflows/
│       └── ci.yml        # GitHub Actions CI: lint + test on every push/PR
├── pyproject.toml        # Project metadata, dependencies, ruff & pytest config
└── README.md
```

---

## Payment Event Schema

The `/webhook/payments` endpoint accepts a JSON body with these fields:

| Field            | Type    | Required | Notes                              |
|------------------|---------|----------|------------------------------------|
| `transaction_id` | string  | Yes      | Unique identifier for the event    |
| `amount`         | float   | Yes      | Transaction amount                 |
| `currency`       | string  | Yes      | Exactly 3 characters (e.g. `USD`) |
| `event_type`     | string  | Yes      | e.g. `payment_settled`             |

**Example request:**

```http
POST /webhook/payments
X-Webhook-Token: your-secret-here
Content-Type: application/json

{
  "transaction_id": "txn_001",
  "amount": 99.99,
  "currency": "USD",
  "event_type": "payment_settled"
}
```

**Example success response (`200 OK`):**

```json
{ "status": "ack", "transaction_id": "txn_001" }
```

---

## Tech Stack

| Layer        | Library / Tool                          |
|--------------|-----------------------------------------|
| Web framework | [FastAPI](https://fastapi.tiangolo.com/) >= 0.110 |
| ASGI server   | [Uvicorn](https://www.uvicorn.org/) >= 0.29  |
| Validation    | [Pydantic](https://docs.pydantic.dev/) v2 >= 2.6 |
| Testing       | [pytest](https://pytest.org/) >= 8.0 + [httpx](https://www.python-httpx.org/) >= 0.27 |
| Linting       | [Ruff](https://docs.astral.sh/ruff/) >= 0.4 |
| Python        | >= 3.11                                 |

---

## Setup

```bash
pip install -e ".[dev]"
```

Set the required authentication token — **never hard-code it**:

```bash
export PAYMENTS_WEBHOOK_TOKEN="your-secret-here"
```

See [app/example_env.py](app/example_env.py) for the correct pattern and what NOT to do.

---

## Run

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive docs are auto-generated at `http://127.0.0.1:8000/docs`.

---

## Test

```bash
pytest
```

All 3 tests must pass:

| Test | What it verifies |
|------|-----------------|
| `test_valid_payment` | `200 OK` + correct JSON ack on a valid payload + correct token |
| `test_invalid_token` | `401 Unauthorized` when the wrong token is provided |
| `test_invalid_payload` | `422 Unprocessable Entity` when required fields are missing |

---

## Lint

```bash
ruff check .          # check for violations
ruff check --fix .    # auto-fix safe violations
```

Ruff is configured in `pyproject.toml` to enforce rules `E`, `F`, `W`, and `I` (errors, pyflakes, warnings, imports) targeting Python 3.11 with a line length of 88.

> **Known deliberate violation:** `app/main.py` line 1 has an unused `import json` (ruff rule `F401`).
> This is intentional for demo purposes — a Copilot coding agent can detect and fix it automatically.

---

## CI (GitHub Actions)

Defined in [.github/workflows/ci.yml](.github/workflows/ci.yml).

Triggers on every push to `main` and on all pull requests. Pipeline steps:

1. **Checkout** source
2. **Set up Python 3.11**
3. **Install dependencies** — `pip install -e ".[dev]"`
4. **Lint** — `ruff check .`
5. **Test** — `pytest` (uses `PAYMENTS_WEBHOOK_TOKEN` from GitHub Actions secrets)

---

## Security Notes

- The webhook token is always read from the `PAYMENTS_WEBHOOK_TOKEN` environment variable at request time — never stored in code or config files.
- If the environment variable is unset, all requests are rejected with `401`.
- See [app/example_env.py](app/example_env.py) for guidance on setting the token safely in your shell, CI secrets, or a secrets manager.

Requires repo secret: `PAYMENTS_WEBHOOK_TOKEN`

## Validation Tools (Copilot Coding Agent)

Configured under **Settings → Copilot → Coding agent → Validation tools**:

| Tool | Status |
|---|---|
| Project tests (pytest) | ON |
| Linter (ruff) | ON |
| CodeQL | OFF (toggled off for speed) |
| Advisory database checks | ON |
| Secret scanning | ON |
| Copilot code review | ON |
