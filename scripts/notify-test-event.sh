#!/usr/bin/env bash
# Send a test event to Notify Hub.
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
  echo "[notify-test-event] ERROR: NOTIFY_API_TOKEN が未設定です．.env を確認してください．" >&2
  exit 1
fi

echo "[notify-test-event] http://localhost:${PORT}/api/events にテストイベントを送信します．"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "http://localhost:${PORT}/api/events" \
  -H "Content-Type: application/json" \
  -H "X-Notify-Token: ${TOKEN}" \
  -d '{
    "source": "manual",
    "event_type": "test",
    "severity": "info",
    "title": "Test event from notify-test-event.sh",
    "message": "This event was sent manually to verify the Notify Hub is working."
  }')

if [ "$HTTP_CODE" -eq 201 ]; then
  echo "[notify-test-event] 成功 (HTTP ${HTTP_CODE})"
else
  echo "[notify-test-event] ERROR: HTTP ${HTTP_CODE} が返されました．" >&2
  exit 1
fi
