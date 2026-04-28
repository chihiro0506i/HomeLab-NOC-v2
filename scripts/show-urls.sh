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

HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [ -z "${HOST_IP:-}" ]; then
  HOST_IP="<RaspberryPi-IP>"
fi

echo "Portal      : http://${HOST_IP}:${PORTAL_PORT:-8080}"
echo "Pi-hole     : http://${HOST_IP}:${PIHOLE_WEB_PORT:-8081}/admin"
echo "NetAlertX   : http://${HOST_IP}:${NETALERTX_PORT:-20211}"
echo "Uptime Kuma : http://${HOST_IP}:${UPTIME_KUMA_PORT:-3001}"
