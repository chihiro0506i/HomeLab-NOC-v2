#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
docker compose down
echo "[stop] 停止しました．DNSとして使っている端末がある場合は，端末側DNS設定を戻してください．"
