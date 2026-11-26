#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose up -d --build --wait
echo "Catraca em http://localhost:${WEB_PORT:-8000}"
