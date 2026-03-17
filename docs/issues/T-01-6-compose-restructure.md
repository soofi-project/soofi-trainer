# Task

- user story: [US-01](US-01-infrastructure.md) #57

/label ~UserStory_US-01
/label ~Task
/label ~ToDo
/milestone %Sprint3

# Description

**Docker Compose Stack Restructuring — Includes & Port Reassignment**

The root `docker-compose.yml` has grown to ~420 lines covering 14 services across infrastructure, agents, UI, voice, training, and tooling. Split it into domain-scoped sub-files using Docker Compose `include` and define a consistent, conflict-free port layout.

## Changes

### 1. Split into sub-compose files via `include`

Introduce a thin root `docker-compose.yml` that only declares shared resources (networks, volumes) and pulls in domain files via `include`:

```
docker-compose.yml           ← root: networks, volumes, includes
compose/infra.yml            ← Weaviate, MinIO, PostgreSQL
compose/knowledge.yml        ← Vector MCP, Knowledge Ingestion
compose/agents.yml           ← Advisor, Training Agent, Interaction Agent
compose/training.yml         ← Training Gateway, Training Container
compose/ui.yml               ← Soofi UI, Open WebUI, MCP Inspector
compose/voice.yml            ← STT, TTS
compose/tools.yml            ← N8N
```

Root file example:
```yaml
name: soofi-trainer

include:
  - compose/infra.yml
  - compose/knowledge.yml
  - compose/agents.yml
  - compose/training.yml
  - compose/ui.yml
  - compose/voice.yml
  - compose/tools.yml

networks:
  soofi-network:
    driver: bridge
    name: soofi-network
  soofi-training-network:
    driver: bridge
    name: soofi-training-network

volumes:
  weaviate_data:
  open_webui_data:
  postgres_data:
  n8n_data:
  minio_data:
  training_gateway_data:
```

### 2. Port reassignment

Current ports are assigned ad-hoc. Define a clean range layout:

| Range  | Purpose                | Services |
|--------|------------------------|----------|
| `3xxx` | Web UIs                | Soofi UI `:3001`, Open WebUI `:3000` |
| `5xxx` | Workflow tooling       | N8N `:5678` |
| `6xxx` | Dev/debug tools        | MCP Inspector Client `:6274`, Proxy `:6277` |
| `8xxx` | APIs & databases       | Weaviate `:8070`, Training Gateway `:8099` |
| `8xxx` | Voice services         | STT `:8010`, TTS `:8011` |
| `9xxx` | Object storage         | MinIO API `:9000`, Console `:9001` |

**Proposed reassignments** (any port collisions or gaps to resolve):

| Service | Current | Proposed | Reason |
|---------|---------|----------|--------|
| Weaviate | `8070` | `8070` | keep — already in range |
| MinIO API | `9000` | `9000` | keep |
| MinIO Console | `9001` | `9001` | keep |
| Open WebUI | `3000` | `3000` | keep |
| Soofi UI | `3001` | `3001` | keep |
| STT | `8010` | `8010` | keep |
| TTS | `8011` | `8011` | keep |
| N8N | `5678` | `5678` | keep |
| MCP Inspector Client | `6274` | `6274` | keep |
| MCP Inspector Proxy | `6277` | `6277` | keep |
| Training Gateway | `8099` | `8099` | keep |

> Note: If the `dataset-agent` service (referenced in `interaction-agent` env `AGENT_REGISTRY`) gains an external port, it should be assigned in the `8xxx` API range.

### 3. README / CLAUDE.md updates

- Update the Architecture services table in `CLAUDE.md` to reflect sub-file locations
- Update `README.md` port overview if one exists

## Acceptance Criteria

- [ ] Root `docker-compose.yml` uses `include` directives — no service definitions inline
- [ ] All services are distributed across `compose/*.yml` files by domain
- [ ] `./up.sh` and `./down.sh` work unchanged (no script changes required)
- [ ] `./up.sh --build` rebuilds all services correctly
- [ ] All external ports documented in `.env` remain reachable at the same addresses
- [ ] No port conflicts between services
- [ ] `docker compose config` validates without errors
- [ ] CLAUDE.md Architecture table updated with sub-file locations

# Branches

- `feature/T-01-6-compose-restructure`
