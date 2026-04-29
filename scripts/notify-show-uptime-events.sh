#!/usr/bin/env bash
# Show events from Uptime Kuma.
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

echo "[notify-show-uptime-events] http://localhost:${PORT}/api/events?source=uptime-kuma を取得します…"

curl -s "http://localhost:${PORT}/api/events?source=uptime-kuma" | python3 -m json.tool
