#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[update] 先にバックアップを作成します．"
./scripts/backup.sh

echo "[update] Dockerイメージを更新します．"
docker compose pull pihole netalertx uptime-kuma portal
docker compose build --pull unbound

echo "[update] 再起動します．"
docker compose up -d --remove-orphans

echo "[update] 完了しました．"
