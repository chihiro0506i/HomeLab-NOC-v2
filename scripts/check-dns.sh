#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DOMAIN="${1:-example.com}"
HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [ -z "${HOST_IP:-}" ]; then
  HOST_IP="127.0.0.1"
fi

echo "[check-dns] Pi-hole via host port: @$HOST_IP $DOMAIN"
if command -v dig >/dev/null 2>&1; then
  dig @"$HOST_IP" "$DOMAIN" +short || true
else
  echo "[check-dns] host に dig がないため，コンテナ内から確認します．"
fi

echo
if docker ps --format '{{.Names}}' | grep -qx 'homelab-pihole'; then
  echo "[check-dns] Pi-hole container -> Unbound: @unbound -p 5335 $DOMAIN"
  docker exec homelab-pihole sh -lc "dig @unbound -p 5335 $DOMAIN +short" || true
else
  echo "[check-dns] homelab-pihole コンテナが起動していません．"
fi
