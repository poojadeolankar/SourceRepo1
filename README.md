# Payments Webhook Service

Minimal FastAPI service for inbound bank payment events.

## Setup

```bash
pip install -e ".[dev]"
```

Set the required token — **never hard-code it**:

```bash
export PAYMENTS_WEBHOOK_TOKEN="your-secret-here"
```

See `app/example_env.py` for the correct pattern and what NOT to do.

## Run

```bash
uvicorn app.main:app --reload
```

## Test

```bash
pytest
```

All 3 tests must pass:
- `test_valid_payment` — success path
- `test_invalid_token` — 401 on wrong token
- `test_invalid_payload` — 422 on bad schema

## Lint

```bash
ruff check .          # check
ruff check --fix .    # auto-fix safe violations
```

> **Known deliberate violation:** `app/main.py` line 1 has an unused `import json` (ruff F401).
> This is intentional for the demo — the Copilot coding agent will detect and fix it.

## CI

Workflow: `.github/workflows/ci.yml`

Runs on every push/PR. Steps: install → `ruff check .` → `pytest`

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
