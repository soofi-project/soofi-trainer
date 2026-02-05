# Soofi Trainer - Issues & User Stories

Overview of all user stories and tasks for Phase 1 (MVP).

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  Open WebUI │────▶│   Agent     │────▶│ Vector MCP  │────▶│   Weaviate   │
│  (Chat UI)  │     │ (LangGraph) │     │ (RAG Search)│     │ (Knowledge)  │
└─────────────┘     └─────────────┘     └─────────────┘     └──────────────┘
     :3000               │                   :8113               :8070
                         │
                         ▼
                  ┌─────────────┐
                  │ HuggingFace │
                  │ MCP Server  │
                  │ (Datasets)  │
                  └─────────────┘
```

## User Stories

| ID | Title | Tasks | Description |
|----|-------|-------|-------------|
| US-01 | [Infrastructure](US-01-infrastructure.md) | 4 | Docker stack with Weaviate, Vector MCP, Open WebUI |
| US-02 | [Knowledge Base](US-02-knowledge-base.md) | 3 | Expert knowledge for all LLM specialization methods |
| US-03 | [Agent Architecture](US-03-agent-architecture.md) | 5 | LangGraph agent with decision logic and recommendation reports |
| US-04 | [Integration](US-04-integration.md) | 1 | End-to-end testing and documentation |
| US-05 | [HuggingFace Search](US-05-huggingface-search.md) | 2 | Dataset search on HuggingFace Hub |

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
| T-02-3 | [Knowledge Methods](T-02-3-knowledge-methods.md) | Knowledge about all LLM specialization methods |

### US-03: Agent Architecture

| ID | Title | Description |
|----|-------|-------------|
| T-03-1 | [LangGraph Agent](T-03-1-langgraph-agent.md) | Agent with Vector MCP integration |
| T-03-2 | [Agent Prompts](T-03-2-agent-prompts.md) | German prompts with structured interview |
| T-03-3 | [Starter Prompts](T-03-3-starter-prompts.md) | Quick-start prompts for Open WebUI |
| T-03-4 | [Decision Logic](T-03-4-decision-logic.md) | Decision tree and multi-criteria evaluation |
| T-03-5 | [Recommendation Report](T-03-5-recommendation-report.md) | Structured recommendation output |

### US-04: Integration

| ID | Title | Description |
|----|-------|-------------|
| T-04-1 | [End-to-End Test](T-04-1-end-to-end-test.md) | Test complete flow |

### US-05: HuggingFace Search

| ID | Title | Description |
|----|-------|-------------|
| T-05-1 | [HuggingFace MCP](T-05-1-huggingface-mcp.md) | MCP endpoint for dataset search |
| T-05-2 | [Agent Integration](T-05-2-agent-integration.md) | Agent integration with HuggingFace search |

## Recommended Order

1. **US-01** - Infrastructure (must be first)
2. **US-02** - Knowledge Base (can start parallel with US-03)
3. **US-03** - Agent Architecture
4. **US-05** - HuggingFace Search (can start parallel with US-03)
5. **US-04** - Integration & Testing

## Reference Implementations

- **Weaviate + Vector MCP**: https://gitlab.basys.dfki.dev/hackathon/aas-document-rag/-/blob/master/docker-compose.yml
- **Vector MCP Server**: `dfkibasys/aas-vector-mcp` on Docker Hub
- **HuggingFace Hub API**: https://huggingface.co/docs/huggingface_hub/guides/search

## LLM Specialization Methods (Knowledge Scope)

The agent provides recommendations for these methods:

| Method | Use Case |
|--------|----------|
| Continued Pretraining | Large unlabeled domain data |
| Supervised Fine-Tuning (SFT) | Labeled input-output pairs |
| LoRA | Limited GPU resources |
| QLoRA | Consumer GPUs, large models |
| Prefix Tuning / P-Tuning | Very small datasets |
| Instruction Tuning | Chatbot/Assistant applications |
| RLHF | Human alignment, safety critical |
| DPO | Preference data, simpler than RLHF |
| RAG | Dynamic knowledge, no training |
| Knowledge Distillation | Deployment constraints |

## Total: 5 User Stories, 15 Tasks
