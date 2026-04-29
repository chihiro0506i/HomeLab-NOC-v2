#!/usr/bin/env bash
# Show recent logs from the notify container.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

docker compose logs --tail=100 notify
