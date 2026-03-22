# example_env.py — reference only, NEVER commit real values.
#
# Set this in your shell, CI secrets, or a secrets manager:
#   export PAYMENTS_WEBHOOK_TOKEN="your-secret-here"
#
# Correct usage in code:
#   import os
#   token = os.getenv("PAYMENTS_WEBHOOK_TOKEN")
#
# NEVER do this:
#   TOKEN = "sk-live-abc123"  # hard-coded secret — will be caught by secret scanning
