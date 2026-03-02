#!/bin/bash
# ===========================================
# Soofi Trainer - Start Stack
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  Soofi Trainer - Starting Stack"
echo "========================================"
echo ""

echo "[INFO] Syncing and updating git submodules recursively..."
git submodule sync --recursive
git submodule update --init --recursive

# Load environment variables
source .env 2>/dev/null || true

# Parse args
BUILD_FLAG=""
if [ "$1" == "--build" ]; then
    BUILD_FLAG="--build"
fi

# Start containers (build only if --build passed)
if [ -n "$BUILD_FLAG" ]; then
    echo "[INFO] Building and starting containers..."
else
    echo "[INFO] Starting containers..."
fi
docker compose up -d --wait $BUILD_FLAG

# Check container status
echo ""
echo "[INFO] Container Status:"
docker compose ps

# Print URLs
echo ""
echo "========================================"
echo "  Services are ready!"
echo "========================================"
echo ""
echo "  Open WebUI:       http://localhost:${OPENWEBUI_PORT:-3000}"
echo "  MCP Inspector:    http://localhost:${MCPINSPECTOR_CLIENT_PORT:-6274}/?transport=streamablehttp&serverUrl=http://vector-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=${MCP_AUTH_TOKEN:-dev-stack-token-12345}"
echo "  Weaviate:         http://localhost:${WEAVIATE_PORT:-8070}"
echo "  EDC Provider UI:  http://localhost:8085"
echo "  EDC Consumer UI:  http://localhost:8086"
echo "  AAS UI:           http://localhost:3001"
echo "  Flowise UI:       http://localhost:4040"
echo ""
echo "========================================"
echo ""
echo "To stop the stack, run:  ./down.sh"
echo "To stop and wipe data:  ./down.sh --clean"
echo ""
