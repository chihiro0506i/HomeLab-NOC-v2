#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "[preflight] .env がありません．先に ./scripts/setup.sh を実行してください．" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${PORTAL_PORT:=8080}"
: "${PIHOLE_WEB_PORT:=8081}"
: "${PIHOLE_DNS_PORT:=53}"
: "${NETALERTX_PORT:=20211}"
: "${UPTIME_KUMA_PORT:=3001}"
: "${LAN_INTERFACE:=eth0}"
: "${HOME_SUBNET:=192.168.1.0/24}"

echo "========== homelab-noc preflight =========="
echo "Raspberry Pi IP candidates: $(hostname -I 2>/dev/null || true)"
echo "HOME_SUBNET=$HOME_SUBNET"
echo "LAN_INTERFACE=$LAN_INTERFACE"
echo

if [[ "${PIHOLE_PASSWORD:-}" == "CHANGE_ME_STRONG_PASSWORD" || "${PIHOLE_PASSWORD:-}" == "CHANGE_ME_BEFORE_START" || -z "${PIHOLE_PASSWORD:-}" ]]; then
  echo "[preflight] ERROR: PIHOLE_PASSWORD が初期値のままです．.env を編集してください．" >&2
  exit 1
fi

if [[ "${NOTIFY_API_TOKEN:-}" == "CHANGE_ME_NOTIFY_TOKEN" || -z "${NOTIFY_API_TOKEN:-}" ]]; then
  echo "[preflight] ERROR: NOTIFY_API_TOKEN が初期値のままです．.env を編集してください．" >&2
  exit 1
fi

if [[ -n "${NOTIFY_ENABLE_EXTERNAL_SEND:-}" ]]; then
  echo "[preflight] WARNING: NOTIFY_ENABLE_EXTERNAL_SEND は古い設定名です．NOTIFY_OUTBOUND_ENABLED を使ってください．"
fi

NOTIFY_EFFECTIVE_OUTBOUND_ENABLED="${NOTIFY_OUTBOUND_ENABLED:-}"
if [[ -z "$NOTIFY_EFFECTIVE_OUTBOUND_ENABLED" && -n "${NOTIFY_ENABLE_EXTERNAL_SEND:-}" ]]; then
  NOTIFY_EFFECTIVE_OUTBOUND_ENABLED="$NOTIFY_ENABLE_EXTERNAL_SEND"
fi
if [[ -z "$NOTIFY_EFFECTIVE_OUTBOUND_ENABLED" ]]; then
  NOTIFY_EFFECTIVE_OUTBOUND_ENABLED="true"
fi

NOTIFY_EFFECTIVE_OUTBOUND_ENABLED_LOWER="$(printf '%s' "$NOTIFY_EFFECTIVE_OUTBOUND_ENABLED" | tr '[:upper:]' '[:lower:]')"
if [[ "$NOTIFY_EFFECTIVE_OUTBOUND_ENABLED_LOWER" == "true" && -z "${NOTIFY_NTFY_URL:-}" ]]; then
  echo "[preflight] NOTE: NOTIFY_NTFY_URL が未設定です．Notify Hub はイベント保存のみ行い，外部通知は送信しません．"
fi

if ! ip link show "$LAN_INTERFACE" >/dev/null 2>&1; then
  echo "[preflight] WARNING: LAN_INTERFACE=$LAN_INTERFACE が見つかりません．"
  echo "[preflight]          有線LANなら eth0，Wi-Fiなら wlan0 の可能性があります．"
fi

echo "[preflight] ポート使用状況を確認します．"
if command -v ss >/dev/null 2>&1; then
  ss -lntup 2>/dev/null | grep -E ":(${PIHOLE_DNS_PORT}|${PORTAL_PORT}|${PIHOLE_WEB_PORT}|${NETALERTX_PORT}|${UPTIME_KUMA_PORT})\b" || true
  ss -lnup 2>/dev/null | grep -E ":(${PIHOLE_DNS_PORT})\b" || true
else
  echo "[preflight] ss コマンドが見つからないため，ポート確認をスキップします．"
fi

echo
if command -v systemctl >/dev/null 2>&1; then
  if systemctl is-active --quiet systemd-resolved 2>/dev/null; then
    echo "[preflight] NOTE: systemd-resolved が動いています．環境によっては 53 番ポート競合の原因になります．"
    echo "[preflight]       競合する場合だけ停止・無効化を検討してください．いきなり変更しないでください．"
  fi
fi

echo "[preflight] docker compose の構成解釈を確認します．"
docker compose config >/dev/null

echo "[preflight] OK: 起動前チェックが完了しました．"
