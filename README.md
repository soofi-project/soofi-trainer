# Soofi Trainer

An agentic system that guides users through the LLM specialization process — from use-case analysis to method recommendation (RAG, fine-tuning, etc.).

## Services

### Core Stack

| Service | URL | Description |
|---------|-----|-------------|
| Landing Page | https://localhost:80 | Reveal.js start page with service links |
| Soofi UI | https://localhost:3001 | A2UI chat frontend (Lit Web Components) |
| Open WebUI | https://localhost:3000 | Chat interface |
| Portainer | https://localhost:9090 | Docker management UI |
| Flowise | https://localhost:4040 | Flow-based AI pipeline editor |
| Interaction Agent | docker-internal (interaction-agent:8000) | LangGraph ReAct agent, AG-UI SSE, A2A orchestrator |
| Advisor | docker-internal (advisor:8000) | LangGraph LLM specialization advisor (A2A) |
| Training Agent | docker-internal (training-agent:8000) | LangGraph training job manager (A2A) |
| Training Gateway | https://localhost:8099 | Training job management (MCP) |
| STT | https://localhost:8010 | Speech-to-text service (OpenAI Whisper-1) |
| TTS | https://localhost:8011 | Text-to-speech service (OpenAI tts-1) |
| Vector MCP | docker-internal (vector-mcp:8000) | Knowledge base search (MCP) |
| MCP Inspector | https://localhost:6274 | MCP debugging tool |
| Weaviate | docker-internal (weaviate:8080) | Vector database |
| N8N | https://localhost:5678 | Workflow Automation Platform |
| MinIO | https://localhost:9000 | S3-compatible object storage |
| MinIO Console | https://localhost:9001 | MinIO admin UI |
| Grafana | https://localhost:3002 | Grafana monitoring dashboard |

### AAS Stack (82xx)

| Service | URL | Description |
|---------|-----|-------------|
| AAS WebUI | https://localhost:8280 | BaSyx AAS GUI |
| Mnestix Browser | https://localhost:8281 | Mnestix AAS Browser |
| Mnestix Proxy | https://localhost:8265 | Mnestix reverse proxy |
| AAS Registry | https://localhost:8287 | BaSyx AAS Shell Registry |
| SM Registry | https://localhost:8288 | BaSyx Submodel Registry |
| AAS Environment | https://localhost:8289 | BaSyx AAS Environment (shells + submodels) |
| AAS Discovery | https://localhost:8290 | BaSyx AAS Discovery Service |

### EDC Stack (83xx)

| Service | URL | Description |
|---------|-----|-------------|
| Portal Provider | https://localhost:8380 | EDC Provider UI |
| Portal Consumer | https://localhost:8381 | EDC Consumer UI |
| EDC Provider | https://localhost:8390 | Eclipse Dataspace Connector (Provider) |
| EDC Consumer | https://localhost:8391 | Eclipse Dataspace Connector (Consumer) |
| EDC Consumer MCP | https://localhost:8392 | EDC Consumer MCP Server |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key (or another embedding provider)

### 1. Create secrets file

```bash
cat > ~/.env.secrets << 'EOF'
OPENAI_API_KEY=sk-your-key-here
EOF
```

### 2. Start the stack

```bash
./up.sh              # Start containers (picks up .env changes without rebuild)
./up.sh --build      # Rebuild images and start containers
./up.sh --vllm       # Use H200 backend (local STT/TTS, vLLM via LiteLLM)
```

### 3. Open the UI

- **Landing Page**: https://localhost:80
- **Soofi UI (A2UI)**: https://localhost:3001
- **Chat (Open WebUI)**: https://localhost:3000
- **MCP Inspector**: https://localhost:6274/?transport=streamable-http&serverUrl=http://vector-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345
- **Grafana**: https://localhost:3002

### 4. Try the Soofi UI

Open https://localhost:3001 and ask the agent about LLM specialization methods (RAG, LoRA, QLoRA, SFT, DPO, …). Push-to-talk: hold **Space** to record, release to send. The agent searches the knowledge base and streams a spoken response.

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
| `soofi-trainer_postgres_data` | N8N PostgreSQL database |
| `soofi-trainer_n8n_data` | N8N encryption keys & config |
| `soofi-trainer_prometheus_data` | Prometheus database |
| `soofi-trainer_grafana_data` | Grafana config |
| `soofi-trainer_training_gateway_data` | Training Gateway job state |
| `soofi-trainer_mnestix-database` | Mnestix database |

To delete a single volume (containers must be stopped):

```bash
docker volume rm soofi-trainer_weaviate_data
```

## Configuration

All configuration is in `.env` (committed, no secrets). Secrets are loaded from an external file via `ENV_SECRETS_FILE`.

### Core

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV_SECRETS_FILE` | `~/.env.secrets` | Path to secrets file |
| `LANDING_PAGE_PORT` | `443` | Landing page external port |
| `LANDING_PAGE_HOSTNAME` | `localhost` | Hostname used in slide links |
| `LANDING_PAGE_WATCH_SLIDES` | `true` | Poll slides templates for changes (dev) |
| `EMBEDDING_MODEL` | `openai:text-embedding-3-large` | Embedding model (`provider:model`, e.g. `ollama:bge-m3`) |
| `OLLAMA_HOST` | _(unset)_ | Ollama base URL — only needed for Ollama embedding model |
| `OPENAI_BASE_URL` | _(unset)_ | LLM endpoint override (Ollama / LM Studio / Triton) |

### UI & Voice

| Variable | Default | Description |
|----------|---------|-------------|
| `SOOFI_UI_PORT` | `3001` | Soofi UI (A2UI frontend) port |
| `OPENWEBUI_PORT` | `3000` | Open WebUI port |
| `FLOWISE_PORT` | `4040` | Flowise port |
| `STT_PORT` | `8010` | STT service external port |
| `TTS_PORT` | `8011` | TTS service external port |
| `STT_LANGUAGE` | `de` | Whisper transcription language |
| `TTS_VOICE` | `alloy` | OpenAI TTS voice |
| `TTS_SPEED` | `1.3` | TTS playback speed |
| `VITE_VOICE_CONTROLS_VISIBLE` | `true` | Show on-screen mic button ¹ |
| `VITE_VOICE_ACTIVATION` | `push-to-talk` | Voice activation mode (`push-to-talk` \| `toggle`) ¹ |

### Knowledge & Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `WEAVIATE_COLLECTION` | `SoofiKnowledge` | Weaviate collection name |
| `MINIO_ACCESS_KEY` | `soofi` | MinIO user name |
| `MINIO_SECRET_KEY` | `soofi-password` | MinIO password |
| `MINIO_PORT` | `9000` | MinIO API port |
| `MINIO_CONSOLE_PORT` | `9001` | MinIO Console UI port |

### Agents & Models

| Variable | Default | Description |
|----------|---------|-------------|
| `ADVISOR_MODEL` | `gpt-4o-mini` | LLM model for the advisor agent |
| `INTERACTION_MODEL` | `gpt-4o-mini` | LLM model for the interaction agent |
| `TRAINING_AGENT_MODEL` | `gpt-4o-mini` | LLM model for the training agent |

### Training

| Variable | Default | Description |
|----------|---------|-------------|
| `TRAINING_GATEWAY_PORT` | `8099` | Training Gateway external port |
| `TRAINING_BACKEND` | `docker` | `local` (subprocess) or `docker` (Docker API) |
| `TRAINING_DOCKER_HOST` | _(unset)_ | Remote Docker API URL — leave unset for local socket |
| `TRAINING_GPU_DEVICE` | _(unset)_ | GPU device ID (`all` or e.g. `0`) — empty for no GPU |
| `TRAINING_DEFAULT_DURATION` | `120` | Default simulation duration in seconds |
| `OPENAI_BASE_URL` | _(unset)_ | LLM endpoint override — set in backend profile files (`docker-compose.ollama.yml` etc.), not in `.env` |
|`GRAFANA_VERSION`|`12.3`| Grafana image version |
|`GRAFANA_PORT`|`3002`| Grafana external port |
|`GRAFANA_ADMIN_PASSWORD`|`admin`| Grafana admin password |
|`PROMETHEUS_VERSION`|`v3.10.0`| Prometheus image version |

> ¹ These are Vite build args, not runtime environment variables. Changing them requires a rebuild (`./up.sh --build`).

### MCP Inspector

| Variable | Default | Description |
|----------|---------|-------------|
| `MCPINSPECTOR_CLIENT_PORT` | `6274` | MCP Inspector UI port |
| `MCPINSPECTOR_PROXY_PORT` | `6277` | MCP Inspector proxy port |
| `MCP_AUTH_TOKEN` | `dev-stack-token-12345` | MCP Auth token |

### AAS Stack

| Variable | Default | Description |
|----------|---------|-------------|
| `BASYX_VERSION` | `2.0.0-milestone-08` | BaSyx image version |
| `AAS_HOSTNAME` | `localhost` | Externally reachable hostname for AAS endpoint URLs |
| `AAS_WEBUI_PORT` | `8280` | AAS WebUI port |
| `MNESTIX_BROWSER_PORT` | `8281` | Mnestix Browser port |
| `MNESTIX_PROXY_PORT` | `8265` | Mnestix Proxy port |
| `AAS_REGISTRY_PORT` | `8287` | AAS Shell Registry port |
| `SM_REGISTRY_PORT` | `8288` | Submodel Registry port |
| `AAS_ENVIRONMENT_PORT` | `8289` | AAS Environment port |
| `AAS_DISCOVERY_PORT` | `8290` | AAS Discovery port |

> **Note:** `AAS_HOSTNAME` is used to build the externally-reachable endpoint URLs that are registered in the AAS/Submodel Registry. The browser needs to be able to reach `https://${AAS_HOSTNAME}:${AAS_ENVIRONMENT_PORT}` directly. When changing this, restart all AAS services.

### EDC Stack

| Variable | Default | Description |
|----------|---------|-------------|
| `EDC_MCP_VERSION` | `0.1.0` | EDC Consumer MCP image version |
| `EDC_PORTAL_PROVIDER_PORT` | `8380` | EDC Provider Portal port |
| `EDC_PORTAL_CONSUMER_PORT` | `8381` | EDC Consumer Portal port |
| `EDC_PROVIDER_PORT` | `8390` | EDC Provider public endpoint port |
| `EDC_CONSUMER_PORT` | `8391` | EDC Consumer public endpoint port |
| `EDC_CONSUMER_MCP_PORT` | `8392` | EDC Consumer MCP Server port |

> **Voice config**: `VITE_*` variables are injected at **runtime** via `docker-entrypoint.sh` → `env.js` → `window.__ENV`. Changing them in `.env` only requires a restart (`./up.sh`), not a rebuild. A one-time `./up.sh --build` is needed after upgrading to the entrypoint-based image.

### Voice mapping (H200 / Piper)

| Voice | Model | Language |
|-------|-------|----------|
| `alloy` | thorsten-high | German (male) |
| `echo` | thorsten_emotional-medium | German (male) |
| `fable` | thorsten_emotional-medium | German (male) |
| `nova` | kerstin-low | German (female) |
| `onyx` | lessac-high | English |
| `shimmer` | lessac-high | English |

The UI sends the voice from `VITE_TTS_VOICE_DE` (German) or `VITE_TTS_VOICE_EN` (English) based on the language toggle. German voices get phonetic preprocessing (`TTS_DE_PHONETIC_KEYS`/`VALUES`) to correct English loanword pronunciation in Piper.

## Local Inference

`up.sh` supports backend profiles via compose override files.

```bash
./up.sh                # OpenAI (default)
./up.sh --ollama       # Ollama (local)
./up.sh --lmstudio     # LM Studio (local)
./up.sh --triton       # NVIDIA Triton (H200)
./up.sh --vllm         # vLLM via LiteLLM (H200) — STT/TTS local
```

| Profile | Chat endpoint | Embeddings | STT/TTS | Requires |
|---------|--------------|------------|---------|---------|
| _(default)_ | `api.openai.com` | OpenAI | OpenAI cloud | `OPENAI_API_KEY` in `~/.env.secrets` |
| `--ollama` | Ollama (`localhost:11434`) | Ollama `bge-m3` | OpenAI cloud | Ollama running + models pulled |
| `--lmstudio` | LM Studio (`localhost:1234`) | LM Studio `bge-m3` | OpenAI cloud | LM Studio server running + models loaded |
| `--triton` | Triton (`10.2.10.33:9000`) | OpenAI | OpenAI cloud | Triton running + model loaded, `OPENAI_API_KEY` for embeddings |
| `--vllm` | vLLM via LiteLLM (`10.2.10.33:4000`) | Qwen3-Embedding-8B | H200 local (Piper + Whisper) | H200 inference stack deployed |

To change the model, edit the override file and restart with `./up.sh --ollama` (no `--build` needed).

> **Note:** When switching the embedding model (e.g. from OpenAI to Ollama), the vector dimensions change and existing Weaviate data becomes incompatible. Wipe the volume before restarting:
> ```bash
> ./down.sh --clean
> ./up.sh --ollama
> ```

## Project Structure

```
soofi-trainer/
├── knowledge/              # Markdown knowledge documents + YAML metadata
├── knowledge-ingestion/    # One-shot ingestion container (local build)
├── advisor/                # LangGraph advisor agent (local build)
├── vector-mcp/             # Vector MCP server (local build)
├── soofi-ui/               # A2UI Lit frontend (local build)
├── interaction-agent/      # LangGraph ReAct agent, AG-UI SSE, A2A orchestrator (local build)
├── training-agent/         # LangGraph training agent (local build)
├── stt/                    # Speech-to-text service (local build)
├── tts/                    # Text-to-speech service (local build)
├── training-pipeline/      # Training job orchestration
│   ├── training-container/ # Simulated training workload
│   └── training-gateway/   # MCP server for training job management
├── edc-mcp/                # EDC Consumer MCP server (local build)
├── landingpage/            # Reveal.js landing page (Docker image)
│   ├── Dockerfile
│   └── docker-entrypoint.sh   # envsubst templating + slide watcher
├── compose/                # Domain-scoped compose sub-files
│   ├── admin.yml           # Portainer, Landing Page
│   ├── knowledge.yml       # Weaviate, Vector MCP, MinIO, Ingestion, Advisor
│   ├── training.yml        # Training Agent, Gateway, Container
│   ├── interaction.yml     # Interaction Agent, Soofi UI, STT, TTS
│   ├── tools.yml           # Open WebUI, N8N, MCP Inspector, Flowise
│   ├── aas.yml             # BaSyx AAS stack (82xx ports)
│   ├── edc.yml             # Eclipse Dataspace Connector stack (83xx ports)
│   ├── monitoring.yml      # Grafana, Prometheus
│   ├── admin/
│   │   └── landingpage/content/   # index.html, media/, slides/slides.md
│   └── aas/
│       ├── aasx/           # AASX files loaded by aas-environment on startup
│       └── config/         # BaSyx application.yml configs
├── docker-compose.yml      # Service orchestration (includes compose/)
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

> **Note:** If you enable MinIO on an existing stack, run `./down.sh --clean` first. The source URLs in Weaviate change from relative paths to MinIO URLs, so a fresh ingestion is required.

To re-run ingestion after editing documents:

```bash
docker compose up knowledge-ingestion
```

## AAS Stack

AASX files in `compose/aas/aasx/` are automatically loaded by `aas-environment` on startup and registered in `aas-registry` and `sm-registry`. The endpoint URLs registered use `AAS_HOSTNAME:AAS_ENVIRONMENT_PORT` so they are browser-accessible.

After changing AASX files, restart the AAS services:

```bash
docker compose restart aas-discovery aas-registry sm-registry
docker compose restart aas-environment
```

## N8N

### Import N8N workflows
N8N starts without workflows. Execute the following to load all workflows from `compose/tools/n8n/workflows`

```bash
./compose/tools/n8n/import_workflows.sh
```

### Set up credentials
Workflows that use OpenAI (e.g. Advisor-Agent) need credentials. These are not exported with workflows and must be created manually:

1. Go to **Settings → Credentials → Add Credential → OpenAI API**
2. Set the API Key to `{{ $env.OPENAI_API_KEY }}` (pulls the key from the environment)

### Backup N8N DB
Create a new database dump if the existing SQL cannot be imported anymore (e.g. due to N8N updates).

```bash
docker exec -t postgres_n8n pg_dump -U n8n n8n > n8n-backup-$(date +%Y%m%d-%H%M).sql
```

## OpenWebUI

### Load OpenWebUI functions
OpenWebUI starts without functions (e.g. to connect to N8N). Execute the following to load all functions from `compose/tools/openwebui/functions`

```bash
./compose/tools/openwebui/import_functions.sh
```

## License

MIT License — see [LICENSE](LICENSE)
