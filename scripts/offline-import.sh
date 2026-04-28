#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

IN="${1:-images/homelab-noc-images.tar.gz}"
if [ ! -f "$IN" ]; then
  echo "[offline-import] file not found: $IN" >&2
  exit 1
fi

echo "[offline-import] Dockerイメージを読み込みます: $IN"
gzip -dc "$IN" | docker load
echo "[offline-import] 完了しました．"
