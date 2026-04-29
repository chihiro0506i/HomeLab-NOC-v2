#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[setup] project root: $ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "[setup] ERROR: docker が見つかりません．先に Docker をインストールしてください．" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "[setup] ERROR: docker compose plugin が見つかりません．" >&2
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "[setup] .env を作成しました．PIHOLE_PASSWORD を必ず変更してください．"
else
  echo "[setup] .env は既に存在します．上書きしません．"
fi

mkdir -p \
  data/pihole/etc-pihole \
  data/pihole/logs \
  data/unbound \
  data/netalertx/config \
  data/netalertx/db \
  data/uptime-kuma \
  data/notify \
  backups \
  images \
  secrets

# 権限設定
if command -v sudo >/dev/null 2>&1; then
  # NetAlertX はデフォルト UID/GID 20211 で動く．
  sudo chown -R 20211:20211 data/netalertx 2>/dev/null || true

  # Notify Hub の UID/GID を環境変数から取得（なければ 20212）
  if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
  fi
  sudo chown -R "${NOTIFY_UID:-20212}:${NOTIFY_GID:-20212}" data/notify 2>/dev/null || true
  sudo chmod -R u+rwX,g+rwX data/notify 2>/dev/null || true
fi

chmod -R u+rwX data backups images
chmod +x scripts/*.sh services/unbound/docker-entrypoint.sh

echo "[setup] 完了しました．次に nano .env で PIHOLE_PASSWORD と HOME_SUBNET を確認してください．"
