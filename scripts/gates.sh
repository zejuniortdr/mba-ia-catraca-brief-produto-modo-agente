#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
P="$(basename "$PWD")-gates"
trap 'docker compose -p "$P" down -v --remove-orphans >/dev/null 2>&1' EXIT
docker compose -p "$P" --profile test build test
docker compose -p "$P" --profile test run --rm test "$@"
