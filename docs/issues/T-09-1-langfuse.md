# Task

- user story: [US-09](US-09-agent-observability.md)
- depends on: [T-07-6](T-07-6-interaction-agent.md)

/label ~UserStory_US-09
/label ~Task
/label ~ToDo

# Description

**Langfuse: LLM Tracing for Soofi Agents**

Add Langfuse as a local Docker service and wire it into all LangGraph agents via the official
LangChain callback handler. Langfuse uses OpenTelemetry standards and is open-source
(MIT/Apache 2.0). It runs entirely in Docker Compose — no cloud account needed.

## What Langfuse Provides

- Full trace tree per request: every LangGraph node, tool call, and LLM invocation
- Token counts and cost per trace (useful for comparing cloud vs. local model cost)
- Latency breakdown per node (e.g. how long does `search_documents` take?)
- Prompt versions — track which system prompt was active per trace
- Web UI at `http://localhost:3002` (or configurable port)

## Docker Compose Setup

Langfuse v3 requires Postgres and ClickHouse. Add to `docker-compose.yml`:

```yaml
langfuse:
  image: langfuse/langfuse:latest
  container_name: langfuse
  restart: unless-stopped
  ports:
    - "${LANGFUSE_PORT}:3000"
  environment:
    DATABASE_URL: postgresql://langfuse:langfuse@langfuse-db:5432/langfuse
    CLICKHOUSE_URL: http://langfuse-clickhouse:8123
    NEXTAUTH_URL: http://localhost:${LANGFUSE_PORT}
    NEXTAUTH_SECRET: ${LANGFUSE_SECRET}
    SALT: ${LANGFUSE_SALT}
  depends_on:
    langfuse-db:
      condition: service_healthy
  networks:
    - soofi-network

langfuse-db:
  image: postgres:16-alpine
  container_name: langfuse-db
  restart: unless-stopped
  environment:
    POSTGRES_USER: langfuse
    POSTGRES_PASSWORD: langfuse
    POSTGRES_DB: langfuse
  volumes:
    - langfuse-db-data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U langfuse"]
    interval: 10s
    timeout: 5s
    retries: 5
  networks:
    - soofi-network
```

Note: Evaluate whether ClickHouse is required for the self-hosted version or whether Postgres
alone suffices for our scale (low traffic, demo use).

## LangGraph Integration

Install `langfuse` in both `interaction-agent` and `advisor` Python packages:

```toml
# pyproject.toml dependencies
"langfuse>=2.0"
```

Configure the callback handler via environment variables (no code change needed for
LangChain/LangGraph — just set env vars):

```bash
LANGFUSE_HOST=http://langfuse:3000
LANGFUSE_PUBLIC_KEY=...    # from Langfuse UI after first setup
LANGFUSE_SECRET_KEY=...    # from Langfuse UI after first setup
```

With `LANGFUSE_HOST` set, the `langfuse` package auto-instruments LangChain via the
`CallbackHandler`. For explicit control:

```python
from langfuse.callback import CallbackHandler
handler = CallbackHandler()
# Pass to graph.astream_events(..., config={"callbacks": [handler]})
```

## .env Additions

```
LANGFUSE_PORT=3002
LANGFUSE_SECRET=change-me-in-production
LANGFUSE_SALT=change-me-in-production
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

## Acceptance Criteria

- [ ] Langfuse Docker service starts and web UI is accessible at configured port
- [ ] Interaction Agent traces appear in Langfuse (nodes, tool calls, LLM calls)
- [ ] Advisor traces appear in Langfuse (RAG search + generation latency visible)
- [ ] Token counts shown per trace
- [ ] Traces correlate across agents (shared trace ID for one user request)
- [ ] Service added to `docker-compose.yml` with health check
- [ ] `LANGFUSE_HOST` / keys configurable via `.env` / secrets file

# Branches

- feature/T-09-1-langfuse
