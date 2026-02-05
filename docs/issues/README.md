# Soofi Trainer - Issues & User Stories

Overview of all user stories and tasks for Phase 1.

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  Open WebUI │────▶│   Agent     │────▶│ Vector MCP  │────▶│   Weaviate   │
│  (Chat UI)  │     │ (LangGraph) │     │ (RAG Search)│     │ (Knowledge)  │
└─────────────┘     └─────────────┘     └─────────────┘     └──────────────┘
     :3000                                   :8113               :8070
```

## User Stories

| ID | Title | Tasks | Description |
|----|-------|-------|-------------|
| US-01 | [Infrastructure](US-01-infrastructure.md) | 4 | Docker stack with Weaviate, Vector MCP, Open WebUI |
| US-02 | [Knowledge Base](US-02-knowledge-base.md) | 2 | RAG/Fine-Tuning expert knowledge for the agent |
| US-03 | [Agent Architecture](US-03-agent-architecture.md) | 3 | LangGraph agent with Vector MCP integration |
| US-04 | [Integration](US-04-integration.md) | 1 | End-to-end testing and documentation |

## Tasks

### US-01: Infrastructure

| ID | Title | Description |
|----|-------|-------------|
| T-01-1 | [Docker-Compose Foundation](T-01-1-docker-compose-foundation.md) | Weaviate, Vector MCP, MCP Inspector |
| T-01-2 | [Open WebUI Setup](T-01-2-open-webui-setup.md) | Chat interface configuration |
| T-01-3 | [Stack Management Scripts](T-01-3-stack-management-scripts.md) | up.sh, down.sh |
| T-01-4 | [GitLab CI](T-01-4-gitlab-ci.md) | CI/CD pipeline for builds and tests |

### US-02: Knowledge Base

| ID | Title | Description |
|----|-------|-------------|
| T-02-1 | [Knowledge Collection](T-02-1-knowledge-collection.md) | Weaviate schema setup |
| T-02-2 | [Knowledge Ingestion](T-02-2-knowledge-ingestion.md) | Ingest RAG/Fine-Tuning docs |

### US-03: Agent Architecture

| ID | Title | Description |
|----|-------|-------------|
| T-03-1 | [LangGraph Agent](T-03-1-langgraph-agent.md) | Agent with Vector MCP integration |
| T-03-2 | [Agent Prompts](T-03-2-agent-prompts.md) | German prompts for conversation |
| T-03-3 | [Starter Prompts](T-03-3-starter-prompts.md) | Quick-start prompts for Open WebUI |

### US-04: Integration

| ID | Title | Description |
|----|-------|-------------|
| T-04-1 | [End-to-End Test](T-04-1-end-to-end-test.md) | Test complete flow |

## Recommended Order

1. **US-01** - Infrastructure (must be first)
2. **US-02** - Knowledge Base (can start parallel with US-03)
3. **US-03** - Agent Architecture
4. **US-04** - Integration & Testing

## Reference Implementations

- **Weaviate + Vector MCP**: https://gitlab.basys.dfki.dev/hackathon/aas-document-rag/-/blob/master/docker-compose.yml
- **Vector MCP Server**: `dfkibasys/aas-vector-mcp` on Docker Hub

## Total: 4 User Stories, 10 Tasks
