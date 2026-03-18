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
if [ "$1" == "--clean" ]; then
    echo "[INFO] Stopping containers and removing volumes..."
    docker compose down -v
else
    echo "[INFO] Stopping containers..."
    docker compose down
fi

echo ""
echo "========================================"
echo "  Stack is down"
echo "========================================"
echo ""
echo "To start again, run: ./up.sh"
echo ""
