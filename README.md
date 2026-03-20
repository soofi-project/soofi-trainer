# Soofi Trainer

An agentic system that guides users through the LLM specialization process — from use-case analysis to method recommendation (RAG, fine-tuning, etc.).

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Landing Page | http://localhost:80 | Reveal.js start page with service links |
| Soofi UI | http://localhost:3001 | A2UI chat frontend (Lit Web Components) |
| Open WebUI | http://localhost:3000 | Chat interface |
| Portainer | http://localhost:9090 | Docker management UI |
| Interaction Agent | docker-internal (interaction-agent:8000) | LangGraph ReAct agent, AG-UI SSE, A2A orchestrator |
| Advisor | docker-internal (advisor:8000) | LangGraph LLM specialization advisor (A2A) |
| Training Agent | docker-internal (training-agent:8000) | LangGraph training job manager (A2A) |
| STT | http://localhost:8010 | Speech-to-text service (OpenAI Whisper-1) |
| TTS | http://localhost:8011 | Text-to-speech service (OpenAI tts-1) |
| Training Gateway | docker-internal (training-gateway:8000) | Training job management (MCP) |
| Vector MCP | docker-internal (vector-mcp:8000) | Knowledge base search (MCP) |
| MCP Inspector | http://localhost:6274 | MCP debugging tool |
| Weaviate | docker-internal (weaviate:8080) | Vector database |
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
./up.sh              # Start containers (picks up .env changes without rebuild)
./up.sh --build      # Rebuild images and start containers
./up.sh --vllm       # Use H200 backend (local STT/TTS, vLLM via LiteLLM)
```

### 3. Open the UI

- **Landing Page**: http://localhost:80
- **Soofi UI (A2UI)**: http://localhost:3001
- **Chat (Open WebUI)**: http://localhost:3000
- **MCP Inspector**: http://localhost:6274/?transport=streamable-http&serverUrl=http://vector-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345

### 4. Try the Soofi UI

Open http://localhost:3001 and ask the agent about LLM specialization methods (RAG, LoRA, QLoRA, SFT, DPO, …). Push-to-talk: hold **Space** to record, release to send. The agent searches the knowledge base and streams a spoken response.

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

To delete a single volume (containers must be stopped):

```bash
docker volume rm soofi-trainer_weaviate_data
```

## Configuration

All configuration is in `.env` (committed, no secrets). Secrets are loaded from an external file via `ENV_SECRETS_FILE`.

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV_SECRETS_FILE` | `~/.env.secrets` | Path to secrets file |
| `WEAVIATE_VERSION` | `1.36.2` | Weaviate Image version |
| `WEAVIATE_PORT` | `8070` | Weaviate HTTP port |
| `WEAVIATE_COLLECTION` | `SoofiKnowledge` | Weaviate collection name |
| `EMBEDDING_MODEL` | `openai:text-embedding-3-large` | Embedding model (`provider:model`, e.g. `ollama:bge-m3`) |
| `OLLAMA_HOST` | _(unset)_ | Ollama base URL — only needed when using an Ollama embedding model (e.g. `http://host.docker.internal:11434`) |
| `ADVISOR_NAME` | `soofi-advisor` | Model name shown in Open WebUI |
| `ADVISOR_MODEL` | `gpt-4o-mini` | LLM model for the advisor agent |
| `MCPINSPECTOR_VERSION` | `0.18.0` | MCP Inspector Image version |
| `MCPINSPECTOR_CLIENT_PORT` | `6274` | MCP Inspector UI port |
| `MCPINSPECTOR_PROXY_PORT` | `6277` | MCP Inspector proxy port |
| `MCP_AUTH_TOKEN` | `dev-stack-token-12345` | MCP Auth token |
| `SOOFI_UI_PORT` | `3001` | Soofi UI (A2UI frontend) port |
| `OPENWEBUI_VERSION` | `v0.7.2` | Open WebUI Image version|
| `OPENWEBUI_PORT` | `3000` | Open WebUI port |
| `POSTGRES_VERSION` | `18-alpine` | PostgreSQL Image version |
| `LANDING_PAGE_PORT` | `80` | Landing page external port |
| `LANDING_PAGE_HOSTNAME` | `localhost` | Hostname used in slide links |
| `LANDING_PAGE_WATCH_SLIDES` | `true` | Poll slides templates for changes (dev) |
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
| `KNOWLEDGE_BASE_URL` | `/docs` | Base URL for knowledge source links |
| `INTERACTION_MODEL` | `gpt-4o-mini` | LLM model for the interaction agent |
| `TRAINING_AGENT_MODEL` | `gpt-4o-mini` | LLM model for the training agent |
| `STT_PROVIDER` | `openai` | STT provider (`openai`) |
| `STT_LANGUAGE` | `de` | Whisper transcription language |
| `STT_PORT` | `8010` | STT service external port |
| `STT_VERSION` | `0.1.0` | STT service image version |
| `WHISPER_PROMPT_DE` | `Soofi, RAG, LoRA, …` | Domain vocabulary bias for Whisper (German) |
| `WHISPER_PROMPT_EN` | `Soofi, RAG, LoRA, …` | Domain vocabulary bias for Whisper (English) |
| `TTS_PROVIDER` | `openai` | TTS provider (`openai`) |
| `TTS_MODEL` | `tts-1` | TTS model (Piper on H200) |
| `TTS_SPEED` | `1.2` | TTS playback speed |
| `TTS_DE_PHONETIC_KEYS` | _(see .env)_ | Pipe-separated English loanwords for phonetic replacement |
| `TTS_DE_PHONETIC_VALUES` | _(see .env)_ | Pipe-separated German phonetic spellings (aligned 1:1 with KEYS) |
| `TTS_PORT` | `8011` | TTS service external port |
| `TTS_VERSION` | `0.1.0` | TTS service image version |
| `VITE_VOICE_CONTROLS_VISIBLE` | `true` | Show on-screen mic button |
| `VITE_VOICE_ACTIVATION` | `push-to-talk` | Voice activation mode (`push-to-talk` \| `toggle`) |
| `VITE_TTS_VOICE_DE` | `alloy` | TTS voice for German (alloy, echo, fable, nova) |
| `VITE_TTS_VOICE_EN` | `onyx` | TTS voice for English (onyx, shimmer) |
| `TRAINING_BACKEND` | `docker` | Training backend: `local` (subprocess) or `docker` (Docker API) |
| `TRAINING_DOCKER_HOST` | _(unset)_ | Remote Docker API URL — leave unset to use the local socket |
| `TRAINING_IMAGE_NAME` | `soofi-trainer-dummy-training` | Docker image name for training containers |
| `TRAINING_IMAGE_VERSION` | `0.0.1` | Docker image version for training containers |
| `TRAINING_GPU_DEVICE` | _(unset)_ | GPU device ID (`all` or e.g. `0`, empty = no GPU) |
| `TRAINING_DEFAULT_DURATION` | `120` | Default simulation duration in seconds |
| `OPENAI_BASE_URL` | _(unset)_ | LLM endpoint override — set in backend profile files (`docker-compose.ollama.yml` etc.), not in `.env` |

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

Model names and all other backend settings are configured in the respective override file:

- `docker-compose.ollama.yml` — Ollama models, endpoint, embedding model
- `docker-compose.lmstudio.yml` — LM Studio models, endpoint, embedding model
- `docker-compose.triton.yml` — Triton endpoint and model

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
│   ├── src/               # Python source (LangGraph + FastAPI)
│   ├── Dockerfile
│   └── pyproject.toml
├── vector-mcp/             # Vector MCP server (local build)
│   ├── src/vector_mcp/     # Python source
│   ├── Dockerfile
│   └── pyproject.toml
├── soofi-ui/              # A2UI Lit frontend (local build)
│   ├── src/               # TypeScript source (Lit components)
│   ├── Dockerfile
│   └── package.json
├── interaction-agent/     # LangGraph ReAct agent, AG-UI SSE, A2A orchestrator (local build)
│   ├── src/               # Python source (LangGraph + FastAPI)
│   ├── Dockerfile
│   └── pyproject.toml
├── stt/                   # Speech-to-text service (local build)
│   ├── src/               # Python source (FastAPI + OpenAI Whisper)
│   ├── Dockerfile
│   └── pyproject.toml
├── tts/                   # Text-to-speech service (local build)
│   ├── src/               # Python source (FastAPI + OpenAI tts-1)
│   ├── Dockerfile
│   └── pyproject.toml
├── training-pipeline/         # Training job orchestration
│   ├── training-container/    # Simulated training workload
│   └── training-gateway/      # MCP server for training job management
├── landingpage/               # Reveal.js landing page (Docker image)
│   ├── Dockerfile
│   └── docker-entrypoint.sh   # envsubst templating + slide watcher
├── compose/                   # Domain-scoped compose sub-files
│   ├── admin.yml              # Portainer, Landing Page
│   ├── knowledge.yml          # Weaviate, Vector MCP, MinIO, Ingestion
│   ├── training.yml           # Training Agent, Gateway, Container
│   ├── interaction.yml        # Interaction Agent, Soofi UI, STT, TTS
│   ├── tools.yml              # Open WebUI, N8N, MCP Inspector, Weaviate UI
│   └── admin/
│       └── landingpage/
│           └── content/
│               ├── index.html
│               ├── media/     # Logo etc.
│               └── slides/    # slides.md (envsubst template)
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
docker exec -t postgres pg_dump -U n8n n8n > n8n-backup-$(date +%Y%m%d-%H%M).sql
```

## OpenWebUI

### Load OpenWebUI functions
OpenWebUI starts without functions (e.g. to connect to N8N). Execute the following to load all functions from `compose/tools/openwebui/functions`

```bash
./compose/tools/openwebui/import_functions.sh
```

## License

MIT License — see [LICENSE](LICENSE)
