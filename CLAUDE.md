# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Soofi Trainer is an agentic system (by DFKI GmbH) that guides users through LLM specialization — from use-case analysis to method recommendation (RAG vs. fine-tuning) to training job execution. It uses a Docker Compose microservices architecture with Python backends and a Lit-based web UI.

**Language**: German (prompts, UI text, agent responses are in German)

## Commands

### Stack Management
```bash
./up.sh                  # Start all containers
./up.sh --build          # Build & start all containers
./down.sh                # Stop containers
./down.sh --clean        # Stop & remove all volumes
```

### Re-run Knowledge Ingestion
```bash
docker start knowledge-ingestion && docker logs -f knowledge-ingestion
```

### View Service Logs
```bash
docker logs -f interaction-agent
docker logs -f advisor
docker logs -f training-gateway
```

### Code Quality (vector-mcp)
```bash
cd vector-mcp
pip install -e ".[dev]"
black src/               # Format (line-length: 100)
ruff check src/          # Lint (line-length: 100)
mypy src/                # Type checking (strict, disallow_untyped_defs)
pytest                   # Tests
```

### Training Gateway Tests
```bash
cd training-pipeline/training-gateway
pytest                   # Unit + integration tests
pytest tests/e2e/        # End-to-end tests
```

## Architecture

### Services (docker-compose.yml)

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| Weaviate | 8080 | 8070 | Vector database |
| Vector MCP | 8000 | — | Semantic search MCP server (FastMCP + LangChain) |
| Knowledge Ingestion | — | — | One-shot loader for knowledge docs into Weaviate |
| MinIO | 9000 / 9001 | configurable | S3-compatible object storage for training data |
| Advisor | 8000 | — | LangGraph RAG advisor agent (A2A server) |
| Interaction Agent | 8000 | — | LangGraph orchestrator agent (AG-UI SSE) |
| Soofi UI | 80 | 8501 | Lit web component + nginx reverse proxy |
| STT | 8000 | configurable | Speech-to-text service (OpenAI whisper-1) |
| TTS | 8000 | configurable | Text-to-speech service (OpenAI tts-1) |
| Training Gateway | 8000 | configurable | Training job management (Docker-based) |
| Training Container | — | — | Build-only image for LoRA/QLoRA training jobs |
| N8N | 5678 | configurable | Workflow automation |
| Open WebUI | 8080 | 3000 | Alternative chat interface |
| MCP Inspector | 6274 / 6277 | 6274 / 6277 | MCP debugging tool |

All services communicate via `soofi-network` bridge network. Training containers run on a separate `soofi-training-network`.

### Data Flow
```
User (Soofi UI :8501)
  → Interaction Agent (LangGraph, AG-UI SSE)
    → Advisor (LangGraph, A2A) → Vector MCP → Weaviate
    → Training Agent (A2A) → Training Gateway → Training Container
  → STT/TTS (voice pipeline)
```

### Interaction Agent (`interaction-agent/`)
LangGraph ReAct agent — the orchestrator that the UI talks to. Streams responses via AG-UI SSE protocol.

- `src/agent.py` — FastAPI app, AG-UI SSE endpoint, utility LLM (STT refiner, speech text)
- `src/graph.py` — LangGraph `StateGraph` with tools: `ask_advisor_tool`, `ask_training_agent_tool`, `show_agent_card`, `control_doc_viewer`, `control_training_view`
- `src/sse_stream.py` — SSE streaming state machine with URL-safe text emission, tool stream tracking, doc viewer events
- `src/a2a_client.py` — A2A client for advisor and training agent communication
- `src/constants.py` — Shared event keys between graph.py and sse_stream.py
- `src/prompts.py` — System prompt (German)
- `src/speech.py` — Speech text generation for TTS

Key patterns:
- **Streaming**: Uses `adispatch_custom_event()` from `langchain_core.callbacks` to emit custom events in `astream_events(version="v2")`. Do NOT use `get_stream_writer()` — it only works with `stream_mode="custom"`.
- **Tool state injection**: `InjectedState` from `langgraph.prebuilt` injects conversation state into tools (e.g. `control_doc_viewer` validates doc link indices).
- **Doc viewer**: `control_doc_viewer` returns JSON parsed by `_handle_tool_end` in `sse_stream.py` to emit `DOC_VIEWER` SSE events.

### Advisor (`advisor/`)
LangGraph RAG agent — answers domain questions using knowledge documents from Weaviate.

- `src/server.py` — A2A server setup
- `src/a2a_handler.py` — A2A AgentExecutor, streams LLM tokens + search status events
- `src/graph.py` — LangGraph agent with `search_documents` tool (via Vector MCP)
- `src/prompts.py` — Advisor system prompt (German)
- `src/tools.py` — MCP tool definitions

Event envelope: `{"__soofi_event": "search_status", "text": "..."}` — JSON-wrapped to distinguish from text chunks in A2A streaming.

### Soofi UI (`soofi-ui/`)
Lit web component (`<soofi-chat>`) with AG-UI SSE client, voice controls, and doc viewer panel.

- `src/main.ts` — Single-file Lit component with all styles, state, and rendering
- `nginx.conf` — Reverse proxy routing `/api/` to interaction-agent, `/api/stt/` to STT, `/api/tts/` to TTS, `/docs/` to MinIO
- `docker-entrypoint.sh` — Generates `env.js` from environment variables at container start (runtime VITE_* injection)
- `Dockerfile` — Two-stage build (node → nginx), ENTRYPOINT runs entrypoint.sh

### Training Pipeline (`training-pipeline/`)
- `training-gateway/` — FastAPI service managing training jobs via Docker containers
- `training-container/` — Docker image for LoRA/QLoRA training execution

### Vector MCP Server (`vector-mcp/`)
Python package (`soofi-vector-mcp`) built with FastMCP. Exposes Weaviate as MCP tools:
- `search_documents` — Semantic search with metadata filters
- `list_metadata` — Discover available filter values

Embedding model configurable via `EMBEDDING_MODEL` env var in `provider:model` format.

### Voice Pipeline (`stt/`, `tts/`)
- `stt/src/server.py` — `POST /transcribe` (multipart), OpenAI whisper-1, language-specific prompts (`WHISPER_PROMPT_DE`/`WHISPER_PROMPT_EN`), phantom-prefix hallucination filter, 25 MB upload limit
- `tts/src/server.py` — `POST /synthesize` (JSON `{text, voice, language}`), OpenAI tts-1, `TTS_SPEED` configurable, German phonetic preprocessing (`TTS_DE_PHONETIC_KEYS`/`VALUES`)

### Soofi UI runtime env injection (`soofi-ui/`)
VITE_* variables (voice controls, TTS voice selection) are injected at **runtime** — no rebuild needed:
- `docker-entrypoint.sh` generates `/usr/share/nginx/html/env.js` with `window.__ENV` from container environment variables on every start
- `index.html` loads `env.js` before `main.ts`
- `main.ts` reads `window.__ENV` first, falls back to `import.meta.env` (build-time), then hardcoded defaults
- Build-time ARGs in Dockerfile are kept as fallback for `npm run dev` (local development without Docker)

## Configuration

- `.env` — Committed config (no secrets). All ports, collection names, model config.
- `~/.env.secrets` — External secrets file (path configurable via `ENV_SECRETS_FILE`). Must contain `OPENAI_API_KEY` (or other provider key).
- Secrets are loaded in docker-compose via `env_file` directive.

## Project Tracking

Issue docs live in `docs/issues/` as markdown files, organized by user stories (US-01 through US-07) with sub-tasks (T-xx-x). Branch naming follows `feature/T-xx-x-description` pattern.

## Code Review Workflow

- Use the `code-review:code-review` skill (`Skill` tool) — never review manually
- Post inline comments for all issues with confidence score **≥ 75**
- Post valid issues with score **< 75** as a single general comment at the end of the MR (Sammelkommentar)
- **Always ask for explicit approval before posting any comment** — never post without the user releasing it
- GitLab API: `curl --header "PRIVATE-TOKEN: ..." https://mrk40.dfki.de/api/v4/projects/519/...`
- GitLab token in `~/.env.secrets` (field: `GITLAB_KEY`)

## Python Standards

- Python >= 3.11 required
- Black + Ruff with line-length 100
- MyPy strict mode (`disallow_untyped_defs = true`)
- Target version: py311
