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
echo "  --- Core ---"
echo "  Landing Page:     http://localhost:${LANDING_PAGE_PORT}"
echo "  Soofi UI:         http://localhost:${SOOFI_UI_PORT}"
echo "  Open WebUI:       http://localhost:${OPENWEBUI_PORT}"
echo "  Flowise:          http://localhost:${FLOWISE_PORT}"
echo "  Portainer:        http://localhost:${PORTAINER_PORT}"
echo "  N8N:              http://localhost:${N8N_EXTERNAL_PORT}"
echo "  MinIO Console:    http://localhost:${MINIO_CONSOLE_PORT}/browser/${MINIO_BUCKET} (${MINIO_ACCESS_KEY} | ${MINIO_SECRET_KEY})"
echo "  Training Gateway: http://localhost:${TRAINING_GATEWAY_PORT}"
echo "  Grafana:          http://localhost:${GRAFANA_PORT}"
echo ""
echo "  --- AAS Stack ---"
echo "  AAS WebUI:        http://localhost:${AAS_WEBUI_PORT}"
echo "  Mnestix Browser:  http://localhost:${MNESTIX_BROWSER_PORT}"
echo "  AAS Environment:  http://localhost:${AAS_ENVIRONMENT_PORT}"
echo "  AAS Registry:     http://localhost:${AAS_REGISTRY_PORT}"
echo "  SM Registry:      http://localhost:${SM_REGISTRY_PORT}"
echo "  AAS Discovery:    http://localhost:${AAS_DISCOVERY_PORT}"
echo ""
echo "  --- EDC Stack ---"
echo "  Portal Provider:  http://localhost:${EDC_PORTAL_PROVIDER_PORT}"
echo "  Portal Consumer:  http://localhost:${EDC_PORTAL_CONSUMER_PORT}"
echo "  EDC Provider:     http://localhost:${EDC_PROVIDER_PORT}"
echo "  EDC Consumer:     http://localhost:${EDC_CONSUMER_PORT}"
echo "  EDC Consumer MCP: http://localhost:${EDC_CONSUMER_MCP_PORT}"
echo ""
echo "  --- MCP Inspector ---"
echo "  Vector:           http://localhost:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://vector-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=${MCP_AUTH_TOKEN}"
echo "  Training Gateway: http://localhost:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://training-gateway:8000/mcp/&MCP_PROXY_AUTH_TOKEN=${MCP_AUTH_TOKEN}"
echo "  EDC Consumer MCP: http://localhost:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://edc-consumer-mcp:8081/mcp/&MCP_PROXY_AUTH_TOKEN=${MCP_AUTH_TOKEN}"
echo ""
echo "========================================"
echo ""
echo "To stop the stack, run:  ./down.sh"
echo "To stop and wipe data:  ./down.sh --clean"
echo ""
