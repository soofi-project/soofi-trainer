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
PROFILE_FLAGS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --build)    BUILD_FLAG="--build" ;;
        --chatgpt)  BACKEND_OVERRIDE="chatgpt" ;;
        --ollama)   BACKEND_OVERRIDE="ollama" ;;
        --lmstudio) BACKEND_OVERRIDE="lmstudio" ;;
        --triton)   BACKEND_OVERRIDE="triton" ;;
        --vllm)     BACKEND_OVERRIDE="vllm" ;;
        --profile)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                echo "[ERROR] --profile requires a value"
                echo "[HINT]  Usage: --profile <name>  (can be repeated for multiple profiles)"
                exit 1
            fi
            PROFILE_FLAGS="$PROFILE_FLAGS --profile $1"
            ;;
        --profile=*)
            PROFILE_FLAGS="$PROFILE_FLAGS --profile ${1#--profile=}"
            ;;
        --*)
            echo "[ERROR] Unknown flag: $1"
            echo "[HINT]  Available flags: --build, --chatgpt, --ollama, --lmstudio, --triton, --vllm, --profile <name>"
            exit 1
            ;;
    esac
    shift
done

# Default to "local" profile if none specified
if [ -z "$PROFILE_FLAGS" ]; then
    PROFILE_FLAGS="--profile local"
    echo "[INFO] No profile specified — using default: local"
fi

# Build compose file args
COMPOSE_FILES=(-f docker-compose.yml)
if [ "$BACKEND_OVERRIDE" != "chatgpt" ]; then
    OVERRIDE_FILE="docker-compose.${BACKEND_OVERRIDE}.yml"
    if [ ! -f "$OVERRIDE_FILE" ]; then
        echo "[ERROR] Override file not found: $OVERRIDE_FILE"
        echo "[HINT]  Available backends: --chatgpt (default), --ollama, --lmstudio, --triton, --vllm"
        exit 1
    fi
    echo "[INFO] Backend profile: $BACKEND_OVERRIDE"
    COMPOSE_FILES+=(-f "$OVERRIDE_FILE")
fi

# Log active Docker profiles
if [ -n "$PROFILE_FLAGS" ]; then
    echo "[INFO] Docker profiles:$(echo "$PROFILE_FLAGS" | sed 's/--profile/,/g' | tr -d ' ')"
fi

# Start containers (build only if --build passed)
if [ -n "$BUILD_FLAG" ]; then
    echo "[INFO] Building and starting containers..."
else
    echo "[INFO] Starting containers..."
fi
docker compose "${COMPOSE_FILES[@]}" $PROFILE_FLAGS up -d --wait --remove-orphans $BUILD_FLAG

# Check container status
echo ""
echo "[INFO] Container Status:"
docker compose "${COMPOSE_FILES[@]}" $PROFILE_FLAGS ps

# Print URLs
echo ""
echo "========================================"
echo "  Services are ready!"
echo "========================================"
echo ""
echo "  --- Core ---"
echo "  Landing Page:     https://localhost:${LANDING_PAGE_PORT}"
echo "  Soofi UI:         https://localhost:${SOOFI_UI_PORT}"
echo "  Portainer:        https://localhost:${PORTAINER_PORT}"
echo "  MinIO Console:    https://localhost:${MINIO_CONSOLE_PORT}/browser/${MINIO_BUCKET} (${MINIO_ACCESS_KEY} | ${MINIO_SECRET_KEY})"
echo "  Training Gateway: https://localhost:${TRAINING_GATEWAY_PORT}"
echo "  Grafana:          https://localhost:${GRAFANA_PORT}"
echo ""
echo "  --- AAS Stack ---"
echo "  AAS WebUI:        https://localhost:${AAS_WEBUI_PORT}"
echo "  Mnestix Browser:  https://localhost:${MNESTIX_BROWSER_PORT}"
echo "  AAS Environment:  https://localhost:${AAS_ENVIRONMENT_PORT}"
echo "  AAS Registry:     https://localhost:${AAS_REGISTRY_PORT}"
echo "  SM Registry:      https://localhost:${SM_REGISTRY_PORT}"
echo "  AAS Discovery:    https://localhost:${AAS_DISCOVERY_PORT}"
echo ""
echo "  --- EDC Stack ---"
echo "  Portal Provider:  https://localhost:${EDC_PORTAL_PROVIDER_PORT}"
echo "  Portal Consumer:  https://localhost:${EDC_PORTAL_CONSUMER_PORT}"
echo "  EDC Provider:     https://localhost:${EDC_PROVIDER_PORT}"
echo "  EDC Consumer:     https://localhost:${EDC_CONSUMER_PORT}"
echo "  EDC Consumer MCP: https://localhost:${EDC_CONSUMER_MCP_PORT}"
echo ""
echo "  --- MCP Inspector ---"
echo "  Vector:           https://localhost:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://vector-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=${MCP_AUTH_TOKEN}"
echo "  Training Gateway: https://localhost:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://training-gateway:8000/mcp/&MCP_PROXY_AUTH_TOKEN=${MCP_AUTH_TOKEN}"
echo "  EDC Consumer MCP: https://localhost:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://edc-consumer-mcp:8081/mcp/&MCP_PROXY_AUTH_TOKEN=${MCP_AUTH_TOKEN}"
echo "  Huggingface:      https://localhost:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://huggingface-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=${MCP_AUTH_TOKEN}"
echo ""
echo "========================================"
echo ""
echo "To stop the stack, run:  ./down.sh"
echo "To stop and wipe data:  ./down.sh --clean"
echo ""
