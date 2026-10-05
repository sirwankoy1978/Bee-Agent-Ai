#!/usr/bin/env bash
# Remove the webhook and drop queued updates (switches the bot to polling mode).
set -euo pipefail

TELEGRAM_TOKEN="${TELEGRAM_TOKEN:-$(python - <<'EOF'
from bee.config import get_settings; print(get_settings().telegram_token)
EOF
)}"

curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/deleteWebhook" \
  --data-urlencode "drop_pending_updates=true"
echo
