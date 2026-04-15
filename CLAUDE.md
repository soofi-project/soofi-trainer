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
Re-create the container so the current backend's env vars take effect (plain `docker start` keeps the env from the original create):
```bash
docker compose -f docker-compose.yml [-f docker-compose.<backend>.yml] \
  up -d --force-recreate knowledge-ingestion
docker logs -f knowledge-ingestion
```

When switching embedding models (e.g. chatgpt → vllm), the Weaviate collection must be dropped first — `source_hash` skips unchanged files and leaves old-dim vectors behind, causing mixed-dimension state. Either `./down.sh --clean` first, or drop just the collection:
```bash
curl -X DELETE http://localhost:8070/v1/schema/SoofiKnowledge
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

### Interaction Agent Tests
```bash
cd interaction-agent
pytest tests/            # Pure function tests (no external deps)
```

### Advisor Tests
```bash
cd advisor
pytest tests/            # Deduplication logic tests
```

### Training Gateway Tests
```bash
cd training-pipeline/training-gateway
pytest                   # Unit + integration tests
pytest tests/e2e/        # End-to-end tests
```

## Architecture

### Services

The stack is split into domain-scoped sub-files under `compose/`, included by the root `docker-compose.yml`.

**`compose/knowledge.yml`** — RAG knowledge pipeline
| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| Weaviate | 8080 | 8070 | Vector database |
| Vector MCP | 8000 | — | Semantic search MCP server (FastMCP + LangChain) |
| MinIO | 9000 / 9001 | 9000 / 9001 | S3-compatible object storage for knowledge docs |
| Knowledge Ingestion | — | — | One-shot loader for knowledge docs into Weaviate |
| Advisor | 8000 | — | LangGraph RAG advisor agent (A2A server) |

**`compose/training.yml`** — Training pipeline
| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| Training Agent | 8000 | — | LangGraph training agent (A2A server) |
| Training Gateway | 8000 | 8099 | Training job management (Docker-based) |
| Training Container | — | — | Build-only image for LoRA/QLoRA training jobs |

**`compose/interaction.yml`** — User-facing voice UI
| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| Interaction Agent | 8000 | — | LangGraph orchestrator agent (AG-UI SSE) |
| Soofi UI | 80 | 3001 | Lit web component + nginx reverse proxy |
| STT | 8000 | 8010 | Speech-to-text service (OpenAI whisper-1) |
| TTS | 8000 | 8011 | Text-to-speech service (OpenAI tts-1) |

**`compose/tools.yml`** — Dev & automation tooling
| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| PostgreSQL | 5432 | — | N8N database |
| N8N | 5678 | 5678 | Workflow automation |
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
- `src/prompts.py` — System prompts (German + English)
- `src/speech.py` — Speech text generation for TTS

Key patterns:
- **Streaming**: Uses `adispatch_custom_event()` from `langchain_core.callbacks` to emit custom events in `astream_events(version="v2")`. Do NOT use `get_stream_writer()` — it only works with `stream_mode="custom"`.
- **ReAct short-circuit**: `after_tools()` conditional edge skips the second LLM call when a streaming tool (`ask_advisor_tool`, `ask_training_agent_tool`) already delivered the response. Scans ToolMessages in reverse, stops at the AI message boundary.
- **RAG URL store**: `_rag_urls_store` is a module-level `OrderedDict` (LRU-bounded, max 256) keyed by `advisor_context_id`. Stores source URLs so `control_doc_viewer` can reference them across requests. Do NOT use `ContextVar` — it resets per async task.
- **Doc viewer**: `control_doc_viewer` returns JSON parsed by `_handle_tool_end` in `sse_stream.py` to emit `DOC_VIEWER` SSE events. `_extract_tool_text()` handles all ToolMessage content formats (str, list-of-parts, list-of-str).

### Advisor (`advisor/`)
LangGraph RAG agent — answers domain questions using knowledge documents from Weaviate.

- `src/server.py` — A2A server setup
- `src/a2a_handler.py` — A2A AgentExecutor, streams LLM tokens + search status events
- `src/graph.py` — LangGraph agent with `search_documents` tool (via Vector MCP)
- `src/prompts.py` — Advisor system prompt (German)
- `src/tools.py` — MCP tool definitions

Event envelope: `{"__soofi_event": "<type>", ...}` — JSON-wrapped to distinguish from text chunks in A2A streaming. Types: `search_status` (search progress label), `rag_sources` (retrieved documents with scores, deduplicated by file+section).

### Soofi UI (`soofi-ui/`)
Lit web component (`<soofi-chat>`) with AG-UI SSE client, voice controls, and side panel (doc viewer / agent cards / training progress).

- `src/main.ts` — Single-file Lit component with all styles, state, and rendering
- `src/i18n.ts` — Minimal i18n (DE/EN) with `tr()` function

Key patterns:
- **Side panel mutual exclusion**: Doc viewer, agent cards, and training progress share one panel slot. `_dismissSidePanel()` clears all three before opening a new one — last one wins.
- **RAG sources per message**: `RagSource[]` embedded in `ChatMessage`, buffered in `_pendingRagSources` during streaming, flushed to the message on `TOOL_CALL_END`.
- **Streaming end**: `streaming = false` is set at `TOOL_CALL_END` for advisor/training tools (not at `RUN_FINISHED`), because the second LLM call is suppressed server-side.
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
