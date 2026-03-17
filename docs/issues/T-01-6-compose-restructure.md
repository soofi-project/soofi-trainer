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
compose/knowledge.yml        ← Weaviate, Vector MCP, MinIO, Knowledge Ingestion, Advisor Agent
compose/training.yml         ← Training Agent, Training Gateway, Training Container
compose/interaction.yml      ← Interaction Agent, Soofi UI, STT, TTS
compose/tools.yml            ← PostgreSQL, N8N, Open WebUI, MCP Inspector
```

Root file example:
```yaml
name: soofi-trainer

include:
  - compose/knowledge.yml
  - compose/training.yml
  - compose/interaction.yml
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

Ports are documented per compose file to make the layout traceable:

| Compose file | Service | Port | Notes |
|---|---|---|---|
| `knowledge.yml` | Weaviate | `:8070` | Vector DB HTTP API |
| `knowledge.yml` | MinIO API | `:9000` | S3-compatible object storage |
| `knowledge.yml` | MinIO Console | `:9001` | MinIO admin UI |
| `training.yml` | Training Gateway | `:8099` | Training job management API |
| `interaction.yml` | Soofi UI | `:3001` | Voice UI (nginx + Lit) |
| `interaction.yml` | STT | `:8010` | Speech-to-text |
| `interaction.yml` | TTS | `:8011` | Text-to-speech |
| `tools.yml` | Open WebUI | `:3000` | Chat interface |
| `tools.yml` | N8N | `:5678` | Workflow automation |
| `tools.yml` | MCP Inspector Client | `:6274` | MCP debug UI |
| `tools.yml` | MCP Inspector Proxy | `:6277` | MCP debug proxy |

Services without external ports (internal only): Vector MCP, Knowledge Ingestion, Advisor, Interaction Agent, Training Agent, Training Container, PostgreSQL.

> Note: If the `dataset-agent` service gains an external port, it should be assigned in the `8xxx` range alongside Training Gateway.

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
