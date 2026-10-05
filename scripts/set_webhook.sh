#!/usr/bin/env bash
# Register the Telegram webhook (same procedure as docs.agno.com/agent-os/interfaces/telegram/setup,
# just packaged). Requires the public HTTPS tunnel URL of this server.
#
#   NGROK_URL=https://xxxx.ngrok-free.app ./scripts/set_webhook.sh
set -euo pipefail

: "${NGROK_URL:?set NGROK_URL to your public https tunnel URL, e.g. https://abc.ngrok-free.app}"
TELEGRAM_TOKEN="${TELEGRAM_TOKEN:-$(python - <<'EOF'
from bee.config import get_settings; print(get_settings().telegram_token)
EOF
)}"
TELEGRAM_WEBHOOK_SECRET_TOKEN="${TELEGRAM_WEBHOOK_SECRET_TOKEN:-BeeAgent-DevWebhookSecret-01a10cc2}"

curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook" \
  --data-urlencode "url=${NGROK_URL}/telegram/webhook" \
  --data-urlencode "secret_token=${TELEGRAM_WEBHOOK_SECRET_TOKEN}" \
  --data-urlencode 'allowed_updates=["message","edited_message"]'
echo
curl -sS "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getWebhookInfo" | python -m json.tool
