#!/bin/sh
set -eu

mkdir -p /var/lib/unbound
chown -R unbound:unbound /var/lib/unbound || true

# DNSSEC trust anchor を初期化する．
# 初回に外部通信できない場合でも，Unbound自体は起動を試みる．
if [ ! -s /var/lib/unbound/root.key ]; then
  echo "[unbound] initializing DNSSEC trust anchor..."
  unbound-anchor -a /var/lib/unbound/root.key || true
  chown unbound:unbound /var/lib/unbound/root.key 2>/dev/null || true
fi

exec unbound -d -c /etc/unbound/unbound.conf
