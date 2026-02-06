# Task

- user story: #US-01

/label ~UserStory_US-01
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Create Docker-Compose Foundation**

Create the Docker-Compose configuration for the Soofi Trainer stack.

## Services

| Service | Description | Port |
|---------|-------------|------|
| Weaviate | Vector database for agent knowledge (RAG) | 8070 |
| Vector MCP Server | MCP endpoint for semantic search (`dfkibasys/aas-vector-mcp`) | 8113 |
| MCP Inspector | Debugging tool for MCP tools | 5173 |
| Open WebUI | Chat interface for user interaction | 3000 |

## Requirements

- All services defined in a single `docker-compose.yml`
- Weaviate must have a health check so dependent services can wait for it
- Vector MCP Server connects to Weaviate internally
- Environment variables configured via `.env` file
- `.env.example` provided with all required variables (e.g. `OPENAI_API_KEY`, `EMBEDDING_MODEL`)
- `.gitignore` excludes `.env` and other sensitive/generated files

## Acceptance Criteria

- [ ] All four services start successfully with `docker compose up`
- [ ] Weaviate accessible at `localhost:8070`
- [ ] Vector MCP accessible at `localhost:8113`
- [ ] MCP Inspector accessible at `localhost:5173`
- [ ] Open WebUI accessible at `localhost:3000`
- [ ] `.env.example` documents all required environment variables
- [ ] `.gitignore` is in place

# Branches

- feature/US-01-infrastructure
