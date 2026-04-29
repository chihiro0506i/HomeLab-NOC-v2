#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "[start] .env がありません．先に ./scripts/setup.sh を実行してください．" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

if [[ "${PIHOLE_PASSWORD:-}" == "CHANGE_ME_STRONG_PASSWORD" || "${PIHOLE_PASSWORD:-}" == "CHANGE_ME_BEFORE_START" || -z "${PIHOLE_PASSWORD:-}" ]]; then
  echo "[start] ERROR: PIHOLE_PASSWORD が初期値のままです．nano .env で変更してください．" >&2
  exit 1
fi

if [[ "${NOTIFY_API_TOKEN:-}" == "CHANGE_ME_NOTIFY_TOKEN" || -z "${NOTIFY_API_TOKEN:-}" ]]; then
  echo "[start] ERROR: NOTIFY_API_TOKEN が初期値のままです．nano .env で変更してください．" >&2
  exit 1
fi

echo "[start] Docker Compose を起動します．初回はイメージ取得と Unbound build のため時間がかかります．"
docker compose up -d --build

echo "[start] 起動しました．URLは ./scripts/show-urls.sh で確認できます．"
