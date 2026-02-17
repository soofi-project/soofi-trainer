# Task

- user story: [US-01](US-01-infrastructure.md)

/label ~UserStory_US-01
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Create Docker-Compose Foundation**

Create the Docker-Compose configuration for the Soofi Trainer stack. n8n is added to the stack separately in [T-01-3](T-01-3-n8n-chatbot.md).

## Services

| Service | Description | Port |
|---------|-------------|------|
| Weaviate | Vector database for agent knowledge (RAG) | 8070 |
| Vector MCP Server | MCP endpoint for semantic search (`dfkibasys/aas-vector-mcp`) | 8113 |
| MCP Inspector | Debugging tool for MCP tools | 6274 |
| Open WebUI | Chat interface for user interaction | 3000 |

## Requirements

- All services defined in a single `docker-compose.yml`
- Weaviate must have a health check so dependent services can wait for it
- Vector MCP Server connects to Weaviate internally
- `.gitignore` excludes `.env.secrets`, `.env.local` and other sensitive/generated files

## Open WebUI Configuration

- Disable authentication for development
- Persistent data volume for chat history

## Secrets Management

Secrets (e.g. `OPENAI_API_KEY`) are kept outside the repository in a separate file (e.g. `~/.env.secrets`). The path to this file is configured via `ENV_SECRETS_FILE` in `.env`. Services reference the secrets file via the `env_file` section in `docker-compose.yml`.

- `.env` — project configuration and path to secrets file (`ENV_SECRETS_FILE`), committed to the repo (no secrets inside)
- `.env.secrets` — API keys and other secrets, stored outside the repo (e.g. in home directory)

## Acceptance Criteria

- [ ] All services start successfully with `docker compose up`
- [ ] Weaviate accessible at `localhost:8070`
- [ ] Vector MCP accessible at `localhost:8113`
- [ ] MCP Inspector accessible at `localhost:6274`
- [ ] Open WebUI accessible at `localhost:3000`
- [ ] Open WebUI requires no login in development mode
- [ ] Chat history persists across container restarts
- [ ] Secrets are loaded from an external file via `ENV_SECRETS_FILE`
- [ ] No secrets are stored in the repository
- [ ] `.env` is committed to the repo and documents all required variables
- [ ] `.gitignore` excludes `.env.secrets` and `.env.local`

# Branches

- feature/T-01-1-docker-compose-foundation
