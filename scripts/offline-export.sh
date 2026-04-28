#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

mkdir -p images
OUT="images/homelab-noc-images.tar.gz"

echo "[offline-export] 必要なイメージを取得・buildします．"
docker compose pull pihole netalertx uptime-kuma portal
docker compose build unbound

echo "[offline-export] Dockerイメージを保存します．サイズは大きくなります．"
docker save \
  "pihole/pihole:${PIHOLE_TAG:-latest}" \
  "ghcr.io/netalertx/netalertx:${NETALERTX_TAG:-latest}" \
  "louislam/uptime-kuma:${UPTIME_KUMA_TAG:-2}" \
  "nginx:alpine" \
  "homelab-unbound:local" \
  | gzip > "$OUT"

echo "[offline-export] created: $OUT"
