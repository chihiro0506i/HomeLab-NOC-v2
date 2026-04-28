#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p backups
TS="$(date +%Y%m%d-%H%M%S)"
OUT="backups/homelab-noc-backup-${TS}.tar.gz"

echo "[backup] .env と data/ を含むバックアップを作成します．このファイルには秘密情報が含まれる可能性があります．"
tar -czf "$OUT" \
  docker-compose.yml \
  .env \
  portal \
  configs \
  services \
  scripts \
  docs \
  data

echo "[backup] created: $OUT"
echo "[backup] 注意: このバックアップをGitHubや外部ストレージに不用意に公開しないでください．"
