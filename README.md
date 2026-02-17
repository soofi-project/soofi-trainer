# Soofi Trainer

An agentic system that guides users through the LLM specialization process — from use-case analysis to method recommendation (RAG, fine-tuning, etc.).

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Open WebUI | http://localhost:3000 | Chat interface |
| Vector MCP | docker-internal (vector-mcp:8000) | Knowledge base search |
| MCP Inspector | http://localhost:6274 | MCP debugging tool |
| Weaviate | http://localhost:8070 | Vector database |
| N8N | http://localhost:5678 | Workflow Automation Platform |

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
- **MCP Inspector**: http://localhost:6274/?transport=streamable-http&serverUrl=http://vector-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345

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

## Project Structure

```
soofi-trainer/
├── knowledge/              # Markdown knowledge documents + YAML metadata
├── knowledge-ingestion/    # One-shot ingestion container (local build)
├── vector-mcp/             # Vector MCP server (local build)
│   ├── src/vector_mcp/     # Python source
│   ├── Dockerfile
│   └── pyproject.toml
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

The Vector MCP server exposes two tools:

- **`search_documents`** — Semantic search over the knowledge base, with optional metadata filters
- **`list_metadata`** — Discover available metadata fields and values for filtering

### Knowledge base

Knowledge documents live in `knowledge/` as markdown files with YAML metadata. The `knowledge-ingestion` container automatically loads them into Weaviate on `./up.sh`. It runs once, detects changes via SHA-256 hashes, and exits.

To re-run ingestion after editing documents:

```bash
docker compose up knowledge-ingestion
```

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
