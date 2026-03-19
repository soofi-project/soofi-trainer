# User story

- tasks:
  - [T-01-1](T-01-1-docker-compose-foundation.md) #2
  - [T-01-2](T-01-2-stack-management-scripts.md) #3
  - [T-01-3](T-01-3-n8n-chatbot.md) #4
  - [T-01-4](T-01-4-open-webui-healthcheck.md) #20
  - [T-01-5](T-01-5-env-cleanup.md) #42
  - [T-01-6](T-01-6-compose-restructure.md) #57


# Story

*"As a developer, I want to start a complete Docker stack with a single command, so that I can quickly begin development."*

# Description

The infrastructure forms the foundation for the entire Soofi Trainer project. It includes:

- **Weaviate**: Vector database for agent knowledge (RAG)
- **Vector MCP Server**: MCP endpoint for semantic search (`dfkibasys/aas-vector-mcp`)
- **MCP Inspector**: Debugging tool for MCP tools
- **Open WebUI**: Chat interface for user interaction
- **n8n**: Workflow automation platform used as the agent backend

Open WebUI connects to n8n as its backend. n8n provides a simple chatbot workflow that receives user messages from Open WebUI and returns a response. This serves as the initial integration test to verify the end-to-end connection before implementing the full LangGraph agent.

The infrastructure enables starting the complete development environment with a single command (`./up.sh`).

# Acceptance Criteria

- [ ] `./up.sh` starts all services
- [ ] `./down.sh` shuts everything down cleanly
- [ ] Service URLs are displayed after startup
- [ ] Weaviate accessible at localhost:8070
- [ ] Vector MCP Server accessible at localhost:8113
- [ ] MCP Inspector accessible and shows tools
- [ ] Open WebUI accessible at localhost:3000
- [ ] n8n accessible and running
- [ ] Open WebUI connects to n8n as backend
- [ ] A simple chatbot interaction works end-to-end (question via Open WebUI → response via n8n)
