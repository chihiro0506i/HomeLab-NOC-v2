#!/usr/bin/env bash
set -euo pipefail

echo "[detect-network] default route:"
ip route show default || true

echo
echo "[detect-network] interfaces:"
ip -br addr || true

echo
echo "[detect-network] 推測:"
IFACE="$(ip route show default 2>/dev/null | awk '{print $5; exit}')"
IPCIDR="$(ip -o -f inet addr show "$IFACE" 2>/dev/null | awk '{print $4; exit}')"
echo "LAN_INTERFACE=${IFACE:-unknown}"
echo "RaspberryPi_IP_CIDR=${IPCIDR:-unknown}"
echo "HOME_SUBNET は通常，192.168.1.0/24 や 192.168.0.0/24 です．ルータ設定に合わせて .env を編集してください．"
