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

mkdir -p backups
TS="$(date +%Y%m%d-%H%M%S)"
OUT="backups/homelab-noc-backup-${TS}.tar.gz"

tar_cmd=(tar)
if command -v sudo >/dev/null 2>&1; then
  tar_cmd=(sudo tar)
  echo "[backup] sudo tar を使用して，コンテナ所有ファイルも含めて読み取ります．"
fi

notify_backup_event() {
  local status="$1"
  local severity="$2"
  local title="$3"
  local message="$4"
  local dedup_key="$5"

  local port="${NOTIFY_PORT:-8090}"
  local token="${NOTIFY_API_TOKEN:-}"
  if [ -z "$token" ] || [ "$token" = "CHANGE_ME_NOTIFY_TOKEN" ]; then
    echo "[backup] Notify Hub token is not configured; skip backup event."
    return 0
  fi

  local size_bytes="0"
  if [ -f "$OUT" ]; then
    size_bytes="$(wc -c < "$OUT" | tr -d ' ')"
  fi

  local payload
  if command -v python3 >/dev/null 2>&1; then
    payload="$(
      BACKUP_STATUS="$status" \
      BACKUP_SEVERITY="$severity" \
      BACKUP_TITLE="$title" \
      BACKUP_MESSAGE="$message" \
      BACKUP_DEDUP_KEY="$dedup_key" \
      BACKUP_FILE="$OUT" \
      BACKUP_SIZE_BYTES="$size_bytes" \
      BACKUP_TIMESTAMP="$TS" \
      python3 -c 'import json, os
payload = {
    "source": "backup",
    "event_type": os.environ["BACKUP_STATUS"],
    "severity": os.environ["BACKUP_SEVERITY"],
    "title": os.environ["BACKUP_TITLE"],
    "message": os.environ["BACKUP_MESSAGE"],
    "dedup_key": os.environ["BACKUP_DEDUP_KEY"],
    "metadata": {
        "file": os.environ["BACKUP_FILE"],
        "size_bytes": int(os.environ["BACKUP_SIZE_BYTES"]),
        "timestamp": os.environ["BACKUP_TIMESTAMP"],
    },
}
print(json.dumps(payload, ensure_ascii=False))'
    )"
  else
    echo "[backup] WARNING: python3 is not available; skip Notify Hub event."
    return 0
  fi

  local http_code
  http_code="$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "http://localhost:${port}/api/events" \
    -H "Content-Type: application/json" \
    -H "X-Notify-Token: ${token}" \
    -d "$payload" || true)"

  if [ "$http_code" = "201" ]; then
    echo "[backup] Notify Hub event sent: $status"
  else
    echo "[backup] WARNING: failed to send Notify Hub event ($status, HTTP ${http_code:-curl_error})."
  fi
}

on_error() {
  local exit_code="$?"
  notify_backup_event \
    "backup_failed" \
    "error" \
    "HomeLab backup failed" \
    "Backup script failed before creating a complete archive." \
    "backup:failed"
  exit "$exit_code"
}

trap on_error ERR

echo "[backup] .env と data/ を含むバックアップを作成します．このファイルには秘密情報が含まれる可能性があります．"
"${tar_cmd[@]}" -czf "$OUT" \
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

notify_backup_event \
  "backup_success" \
  "info" \
  "HomeLab backup completed" \
  "Backup archive was created successfully." \
  "backup:success:${TS}"
