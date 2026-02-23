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
docker compose up -d --remove-orphans $BUILD_FLAG

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
echo "  Soofi UI:      http://localhost:${SOOFI_UI_PORT}"
echo "  Open WebUI:    http://localhost:${OPENWEBUI_PORT}"
echo "  MCP Inspector: http://localhost:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://vector-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=${MCP_AUTH_TOKEN}"
echo "  Weaviate:      http://localhost:${WEAVIATE_PORT}"
echo "  N8N:           http://localhost:${N8N_EXTERNAL_PORT} (admin@example.com / S8fi-password)"
echo "  MinIO Console: http://localhost:${MINIO_CONSOLE_PORT}/browser/${MINIO_BUCKET}  ($MINIO_ACCESS_KEY | $MINIO_SECRET_KEY)"
echo ""
echo "========================================"
echo ""
echo "To stop the stack, run:  ./down.sh"
echo "To stop and wipe data:  ./down.sh --clean"
echo ""
