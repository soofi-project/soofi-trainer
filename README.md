# Soofi Trainer

An agentic system that guides users through the LLM specialization process — from use-case analysis to method recommendation (RAG, fine-tuning, etc.).

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Open WebUI | http://localhost:3000 | Chat interface |
| Vector MCP | docker-internal (vector-mcp:8000) | Knowledge base search |
| Training Gateway | docker-internal (training-gateway:8000) | Training job management |
| MCP Inspector | http://localhost:6274 | MCP debugging tool |
| Weaviate | http://localhost:8070 | Vector database |
| N8N | http://localhost:5678 | Workflow Automation Platform |
| MinIO | http://localhost:9000 | S3-compatible object storage |
| MinIO Console | http://localhost:9001 | MinIO admin UI |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key (or another embedding provider)

### 1. Create secrets file

```bash
# Create a secrets file outside the repo
cat > ~/.env.secrets << 'EOF'
OPENAI_API_KEY=sk-your-key-here
EOF
```

### 2. Start the stack

```bash
./up.sh              # Start containers
./up.sh --build      # Rebuild and start containers
```

### 3. Open the UI

- **Chat**: http://localhost:3000
- **Vector MCP Inspector**: http://localhost:6274/?transport=streamable-http&serverUrl=http://vector-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345
- **Training MCP Inspector**: http://localhost:6274/?transport=streamable-http&serverUrl=http://training-gateway:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345

### Stop the stack

```bash
./down.sh           # Stop containers
./down.sh --clean   # Stop containers and remove all volumes
```

### Delete individual volumes

The stack uses named Docker volumes (prefixed with `soofi-trainer_`):

| Volume | Content |
|--------|---------|
| `soofi-trainer_weaviate_data` | Weaviate vector database |
| `soofi-trainer_open_webui_data` | Open WebUI settings & chat history |
| `soofi-trainer_minio_data` | MinIO object storage |
| `soofi-trainer_training_gateway_data` | Training Gateway job state (SQLite) |

To delete a single volume (containers must be stopped):

```bash
docker volume rm soofi-trainer_weaviate_data
```

## Configuration

All configuration is in `.env` (committed, no secrets). Secrets are loaded from an external file via `ENV_SECRETS_FILE`.

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV_SECRETS_FILE` | `~/.env.secrets` | Path to secrets file |
| `WEAVIATE_VERSION` | `1.35.7` | Weaviate Image version |
| `WEAVIATE_PORT` | `8070` | Weaviate HTTP port |
| `WEAVIATE_COLLECTION` | `SoofiKnowledge` | Weaviate collection name |
| `EMBEDDING_MODEL` | `openai:text-embedding-3-large` | Embedding model (provider:model) |
| `MCPINSPECTOR_VERSION` | `0.18.0` | MCP Inspector Image version |
| `MCPINSPECTOR_CLIENT_PORT` | `6274` | MCP Inspector UI port |
| `MCPINSPECTOR_PROXY_PORT` | `6277` | MCP Inspector proxy port |
| `MCP_AUTH_TOKEN` | `dev-stack-token-12345` | MCP Auth token |
| `OPENWEBUI_VERSION` | `v0.7.2` | Open WebUI Image version|
| `OPENWEBUI_PORT` | `3000` | Open WebUI port |
| `POSTGRES_VERSION` | `18-alpine` | PostgreSQL Image version |
| `N8N_VERSION` | `2.8.3` | N8N Image version |
| `N8N_HOST` | `localhost` | Host name n8n runs on |
| `N8N_PROTOCOL` | `http` | The protocol used to reach n8n |
| `N8N_EXTERNAL_PORT` | `5678` | The HTTP port n8n runs on |
| `GENERIC_TIMEZONE` | `Europe/Berlin` | The n8n instance timezone |
| `MINIO_VERSION` | `RELEASE.2025-09-07T16-13-09Z` | MinIO image version |
| `MINIO_ACCESS_KEY` | `soofi` | MinIO user name |
| `MINIO_SECRET_KEY` | `soofi-minio-secret` | MinIO password |
| `MINIO_BUCKET` | `knowledge` | MinIO bucket name for knowledge data |
| `MINIO_PORT` | `9000` | MinIO API port |
| `MINIO_CONSOLE_PORT` | `9001` | MinIO Console UI port |
| `KNOWLEDGE_BASE_URL` | `http://localhost:9000/knowledge` | Base URL for knowledge source links |
| `TRAINING_BACKEND` | `local` | Training backend: `local` (subprocess) or `docker` (Docker API) |
| `TRAINING_DOCKER_HOST` | _(unset)_ | Remote Docker API URL — leave unset to use the local socket |
| `TRAINING_IMAGE` | `soofi-trainer-dummy-training:latest` | Docker image for training containers |
| `TRAINING_GPU_DEVICE` | `all` | GPU device ID (`all` or e.g. `0`) |
| `TRAINING_DEFAULT_DURATION` | `120` | Default simulation duration in seconds |

## Project Structure

```
soofi-trainer/
├── knowledge/              # Markdown knowledge documents + YAML metadata
├── knowledge-ingestion/    # One-shot ingestion container (local build)
├── vector-mcp/             # Vector MCP server (local build)
│   ├── src/vector_mcp/     # Python source
│   ├── Dockerfile
│   └── pyproject.toml
├── training-pipeline/      # Training infrastructure
│   ├── training-gateway/   # Training Gateway MCP server
│   │   ├── src/training_gateway/
│   │   ├── tests/          # Pytest test suite (unit, integration, e2e)
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── training-container/ # Training simulator
│       ├── simulate.py
│       └── Dockerfile
├── n8n/
│   ├── initdb/
│   ├── workflows/
│   ├── import_workflows.sh
│   └── init_script.sh
├── openwebui/
│   ├── functions/
│   └── import_functions.sh
├── docker-compose.yml      # Service orchestration
├── up.sh                   # Start stack
├── down.sh                 # Stop stack
├── .env                    # Configuration (no secrets)
└── docs/issues/            # Project tickets
```

## MCP Tools

### Vector MCP

- **`search_documents`** — Semantic search over the knowledge base, with optional metadata filters
- **`list_metadata`** — Discover available metadata fields and values for filtering

### Training Gateway

- **`start_training_job`** — Start a training job for a given specialization method
- **`get_job_status`** — Get current status, phases, and progress of a training job
- **`list_training_jobs`** — List all training jobs, optionally filtered by status
- **`cancel_training_job`** — Cancel a running or queued training job

### Knowledge base

Knowledge documents live in `knowledge/` as markdown files with YAML metadata. The `knowledge-ingestion` container automatically loads them into Weaviate on `./up.sh`. It runs once, detects changes via SHA-256 hashes, and exits.

> **Note:** If you enable MinIO on an existing stack, run `./down.sh --clean` first. The source URLs in Weaviate change from relative paths to MinIO URLs, so a fresh ingestion is required.

To re-run ingestion after editing documents:

```bash
docker compose up knowledge-ingestion
```

## Training Backend

The Training Gateway supports two backends, configured via `TRAINING_BACKEND` in `.env`.

### Local backend (default)

Runs the training script as a subprocess on the gateway container. No Docker access needed. Useful for development.

```env
TRAINING_BACKEND=local
```

### Docker backend — same host

Starts training containers on the same Docker daemon that runs the stack. The gateway container accesses the Docker socket via a volume mount (already configured in `docker-compose.yml`).

```env
TRAINING_BACKEND=docker
# TRAINING_DOCKER_HOST is left unset — uses /var/run/docker.sock
TRAINING_IMAGE=soofi-trainer-training-container:latest
```

Training containers are started as siblings on `soofi-trainer_soofi-network` and call back to `http://training-gateway:8000/webhooks` when done.

### Docker backend — remote host (GPU server)

Points the gateway to a remote Docker daemon, e.g. the H200 GPU server, via SSH or TCP.

```env
TRAINING_BACKEND=docker
TRAINING_DOCKER_HOST=ssh://user@gpu-server
# or: TRAINING_DOCKER_HOST=tcp://gpu-server:2376
TRAINING_IMAGE=soofi/training-container:latest
```

> **Note:** For SSH, the gateway container needs the SSH private key mounted and `ssh-agent` or `~/.ssh/config` configured.

## N8N

### Import N8N workflows
N8N starts without workflows. Execute the following to load all workflows from `n8n/workflows`

```bash
./n8n/import_workflows.sh
```

### Backup N8N DB
Create a new database dump if the existing SQL cannot be imported anymore (e.g. due to N8N updates).

```bash
docker exec -t postgres pg_dump -U n8n n8n > n8n-backup-$(date +%Y%m%d-%H%M).sql
```

## OpenWebUI

### Load OpenWebUI functions
OpenWebUI starts without functions (e.g. to connect to N8N). Execute the following to load all functions from `openwebui/functions`

```bash
./openwebui/import_functions.sh
```

## License

MIT License — see [LICENSE](LICENSE)
