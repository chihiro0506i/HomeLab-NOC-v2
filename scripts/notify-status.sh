#!/usr/bin/env bash
# Check Notify Hub health endpoint.
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

echo "[notify-status] http://localhost:${PORT}/health を確認します．"
curl -sf "http://localhost:${PORT}/health" && echo ""
