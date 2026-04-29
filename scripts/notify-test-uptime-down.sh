#!/usr/bin/env bash
# Simulate an Uptime Kuma "monitor down" event for Pi-hole DNS.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

PORT="${NOTIFY_PORT:-8090}"
TOKEN="${NOTIFY_API_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "[notify-test-uptime-down] ERROR: NOTIFY_API_TOKEN が未設定です．.env を確認してください．" >&2
  exit 1
fi

echo "[notify-test-uptime-down] http://localhost:${PORT}/api/events に monitor_down イベントを送信します．"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "http://localhost:${PORT}/api/events" \
  -H "Content-Type: application/json" \
  -H "X-Notify-Token: ${TOKEN}" \
  -d '{
    "source": "uptime-kuma",
    "event_type": "monitor_down",
    "severity": "critical",
    "title": "Pi-hole DNS is DOWN",
    "message": "Simulated Uptime Kuma monitor down event.",
    "dedup_key": "uptime:pihole_dns:down",
    "metadata": {
      "monitor_name": "Pi-hole DNS",
      "target": "192.168.11.11:53"
    }
  }')

if [ "$HTTP_CODE" -eq 201 ]; then
  echo "[notify-test-uptime-down] 成功 (HTTP ${HTTP_CODE})"
else
  echo "[notify-test-uptime-down] ERROR: HTTP ${HTTP_CODE} が返されました．" >&2
  exit 1
fi
