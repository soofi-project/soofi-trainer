#!/usr/bin/env bash
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
BACKEND_OVERRIDE="chatgpt"
for arg in "$@"; do
    case "$arg" in
        --build)    BUILD_FLAG="--build" ;;
        --chatgpt)  BACKEND_OVERRIDE="chatgpt" ;;
        --ollama)   BACKEND_OVERRIDE="ollama" ;;
        --lmstudio) BACKEND_OVERRIDE="lmstudio" ;;
        --triton) BACKEND_OVERRIDE="triton" ;;
        --vllm) BACKEND_OVERRIDE="vllm" ;;
        --*)
            echo "[ERROR] Unknown flag: $arg"
            echo "[HINT]  Available flags: --build, --chatgpt, --ollama, --lmstudio, --triton, --vllm"
            exit 1
            ;;
    esac
done

# Build compose file args
COMPOSE_FILES="-f docker-compose.yml"
if [ "$BACKEND_OVERRIDE" != "chatgpt" ]; then
    OVERRIDE_FILE="docker-compose.${BACKEND_OVERRIDE}.yml"
    if [ ! -f "$OVERRIDE_FILE" ]; then
        echo "[ERROR] Override file not found: $OVERRIDE_FILE"
        echo "[HINT]  Available backends: --chatgpt (default), --ollama, --lmstudio, --triton, --vllm"
        exit 1
    fi
    echo "[INFO] Backend profile: $BACKEND_OVERRIDE"
    COMPOSE_FILES="$COMPOSE_FILES -f $OVERRIDE_FILE"
fi

# Start containers (build only if --build passed)
if [ -n "$BUILD_FLAG" ]; then
    echo "[INFO] Building and starting containers..."
else
    echo "[INFO] Starting containers..."
fi
docker compose $COMPOSE_FILES up -d --wait --remove-orphans $BUILD_FLAG

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
echo "  Landing Page:  http://localhost:${LANDING_PAGE_PORT}"
echo "  Soofi UI:      http://localhost:${SOOFI_UI_PORT}"
echo "  Open WebUI:    http://localhost:${OPENWEBUI_PORT}"
echo "  Portainer:     http://localhost:${PORTAINER_PORT}"
echo "  N8N:           http://localhost:${N8N_EXTERNAL_PORT}"
echo "  MinIO Console: http://localhost:${MINIO_CONSOLE_PORT}/browser/${MINIO_BUCKET} (${MINIO_ACCESS_KEY} | ${MINIO_SECRET_KEY})"
echo "  MCP Inspector (Vector):          http://localhost:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://vector-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=${MCP_AUTH_TOKEN}"
echo "  MCP Inspector (Training Gateway): http://localhost:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://training-gateway:8000/mcp/&MCP_PROXY_AUTH_TOKEN=${MCP_AUTH_TOKEN}"
echo "  Grafana:           http://localhost:${GRAFANA_PORT}"
echo ""
echo "========================================"
echo ""
echo "To stop the stack, run:  ./down.sh"
echo "To stop and wipe data:  ./down.sh --clean"
echo ""
