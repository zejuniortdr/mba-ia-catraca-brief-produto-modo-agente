#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose down --remove-orphans
docker compose -p "$(basename "$PWD")-gates" down -v --remove-orphans
