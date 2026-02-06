# User Story

- tasks:
  - #T-01-1
  - #T-01-2
  - #T-01-3
  - #T-01-4

/label ~UserStory
/milestone %ProductBacklog

# Story

*"As a developer, I want to start a complete Docker stack with a single command, so that I can quickly begin development."*

# Description

The infrastructure forms the foundation for the entire Soofi Trainer project. It includes:

- **Weaviate**: Vector database for agent knowledge (RAG)
- **Vector MCP Server**: MCP endpoint for semantic search (`dfkibasys/aas-vector-mcp`)
- **MCP Inspector**: Debugging tool for MCP tools
- **Open WebUI**: Chat interface for user interaction

The infrastructure enables starting the complete development environment with a single command (`./up.sh`).

# Acceptance Criteria

- [ ] `./up.sh` starts all services
- [ ] `./down.sh` shuts everything down cleanly
- [ ] Service URLs are displayed after startup
- [ ] Weaviate accessible at localhost:8070
- [ ] Vector MCP Server accessible at localhost:8113
- [ ] MCP Inspector accessible and shows tools
- [ ] Open WebUI accessible at localhost:3000
- [ ] GitLab CI pipeline runs on push/MR
