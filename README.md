# Soofi Trainer

An agentic system that guides users through the LLM specialization process — from use-case analysis to method recommendation (RAG, fine-tuning, etc.).

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Open WebUI | http://localhost:3000 | Chat interface |
| Vector MCP | docker-internal (vector-mcp:8000) | Knowledge base search |
| MCP Inspector | http://localhost:6274 | MCP debugging tool |
| Weaviate | http://localhost:8070 | Vector database |

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
- **MCP Inspector**: http://localhost:6274/?transport=streamablehttp&serverUrl=http://vector-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345

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
| `WEAVIATE_PORT` | `8070` | Weaviate HTTP port |
| `WEAVIATE_COLLECTION` | `SoofiKnowledge` | Weaviate collection name |
| `MCPINSPECTOR_CLIENT_PORT` | `6274` | MCP Inspector UI port |
| `MCPINSPECTOR_PROXY_PORT` | `6277` | MCP Inspector proxy port |
| `EMBEDDING_MODEL` | `openai:text-embedding-3-large` | Embedding model (provider:model) |
| `OPENWEBUI_PORT` | `3000` | Open WebUI port |

## Project Structure

```
soofi-trainer/
├── vector-mcp/             # Vector MCP server (local build)
│   ├── src/vector_mcp/     # Python source
│   ├── Dockerfile
│   └── pyproject.toml
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

### Load test data

The knowledge base starts empty. To seed sample documents for testing:

```bash
docker exec vector-mcp python scripts/seed_testdata.py
```
This creates the collection (if needed) and inserts test documents with real embeddings.

### Import N8N workflows
N8N starts without workflows. Execute the following to load all workflows from `n8n/workflows`

```bash
./n8n/import_workflows.sh

```

### Load OpenWebUI functions
OpenWebUI starts without functions (e.g. to connect to N8N). Execute the following to load all functions from `openwebui/functions`

```bash
./openwebui/import_functions.sh
```

### Backup N8N DB

```bash
docker exec -t postgres pg_dump -U n8n n8n > n8n-backup-$(date +%Y%m%d-%H%M).sql
```


## License

MIT License — see [LICENSE](LICENSE)
