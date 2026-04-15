#!/usr/bin/env bash
# ===========================================
# Soofi Trainer - Stop Stack
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  Soofi Trainer - Stopping Stack"
echo "========================================"
echo ""

# Stop containers (optionally remove volumes)
# Pass every known profile so services started under --profile are included.
# Docker Compose has no wildcard; unused profiles are harmless.
PROFILES="--profile local --profile domain"

if [ "$1" == "--clean" ]; then
    echo "[INFO] Stopping containers and removing volumes..."
    docker compose $PROFILES down -v --remove-orphans
elif [ -n "$1" ]; then
    echo "[ERROR] Unknown option: $1"
    echo "Usage: ./down.sh [--clean]"
    exit 1
else
    echo "[INFO] Stopping containers..."
    docker compose $PROFILES down --remove-orphans
fi

echo ""
echo "========================================"
echo "  Stack is down"
echo "========================================"
echo ""
echo "To start again, run: ./up.sh"
echo ""