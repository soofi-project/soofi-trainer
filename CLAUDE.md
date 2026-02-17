# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Soofi Trainer is an agentic system (by DFKI GmbH) that guides users through LLM specialization — from use-case analysis to method recommendation (RAG vs. fine-tuning). It uses a Docker Compose microservices architecture with Python backends.

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

### Vector MCP Local Development
```bash
cd vector-mcp
pip install -e ".[dev]"
python -m vector_mcp.server
```

### Code Quality (vector-mcp)
```bash
black src/               # Format (line-length: 100)
ruff check src/          # Lint (line-length: 100)
mypy src/                # Type checking (strict, disallow_untyped_defs)
pytest                   # Tests
```

## Architecture

### Services (docker-compose.yml)

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| Weaviate | 8080 | 8070 | Vector database (v1.35.7) |
| Vector MCP | 8000 | — | Semantic search MCP server (FastMCP + LangChain) |
| Knowledge Ingestion | — | — | One-shot loader for knowledge docs into Weaviate |
| MCP Inspector | 6274 / 6277 | 6274 / 6277 | MCP debugging tool (UI + Proxy) |
| Open WebUI | 8080 | 3000 | Chat interface (v0.7.2) |

All services communicate via `soofi-network` bridge network. Weaviate has a healthcheck; vector-mcp depends on it. Vector MCP has no external port — it is only reachable by other services via Docker network (`vector-mcp:8000`).

### Data Flow
```
User (Open WebUI :3000) → Agent (LangGraph) → Vector MCP (vector-mcp:8000) → Weaviate (:8070)
```

### Agent (`agent/`)
LangGraph state machine with FastAPI HTTP server. States flow linearly:
`GREETING → ANALYSIS → RECOMMENDATION → CONFIGURATION → EXECUTION → MONITORING → COMPLETED`
(ERROR reachable from any state, recovers to GREETING)

- `server.py` — FastAPI app with `/chat` (POST), `/health`, `/sessions` endpoints. In-memory session storage.
- `graph.py` — LangGraph `StateGraph` with nodes: agent → tools → process → agent loop. Uses `ChatOpenAI` (default: gpt-4o-mini).
- `state.py` — Pydantic models for `AgentState`, `ConversationState`, `UseCaseAnalysis`, `Recommendation`, `TrainingConfig`.
- `prompts.py` — State-specific German prompts.
- `tools.py` — LangChain tool definitions (search_documents, analyze_use_case, recommend_approach, etc.)

### Vector MCP Server (`vector-mcp/`)
Python package (`soofi-vector-mcp`) built with FastMCP. Exposes Weaviate as MCP tools:
- `search_documents` — Semantic search with metadata filters
- `list_metadata` — Discover available filter values

Embedding model is configurable via `EMBEDDING_MODEL` env var in `provider:model` format (e.g., `openai:text-embedding-3-large`, `ollama:nomic-embed-text`). Supported providers: openai, google_genai, voyageai, ollama.

Source lives in `src/vector_mcp/`, installed as package via `pyproject.toml`.

## Configuration

- `.env` — Committed config (no secrets). All ports, collection names, model config.
- `~/.env.secrets` — External secrets file (path configurable via `ENV_SECRETS_FILE`). Must contain `OPENAI_API_KEY` (or other provider key).
- Secrets are loaded in docker-compose via `env_file` directive.

## Project Tracking

Issue docs live in `docs/issues/` as markdown files, organized by user stories (US-01 through US-05) with sub-tasks (T-xx-x). Branch naming follows `feature/T-xx-x-description` pattern.

## Python Standards

- Python ≥ 3.11 required
- Black + Ruff with line-length 100
- MyPy strict mode (`disallow_untyped_defs = true`)
- Target version: py311
