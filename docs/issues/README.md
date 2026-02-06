# Soofi Trainer - Issues & User Stories

Overview of all user stories and tasks for Phase 1 (MVP).

## Architecture Overview

### Sprint 1 (MVP)

n8n serves as a temporary agent backend for initial testing. Open WebUI connects to n8n which runs a simple chatbot workflow.

```
┌─────────────┐     ┌─────────────┐
│  Open WebUI │────▶│     n8n     │
│  (Chat UI)  │     │  (Chatbot)  │
└─────────────┘     └─────────────┘
     :3000

┌─────────────────┐     ┌─────────────┐     ┌──────────────┐
│   Ingestion     │────▶│ Vector MCP  │────▶│   Weaviate   │
│   Container     │     │ (RAG Search)│     │ (Knowledge)  │
└─────────────────┘     └─────────────┘     └──────────────┘
                             :8113               :8070
```

### Target Architecture

n8n is replaced by a LangGraph agent that handles the full conversation flow including knowledge retrieval and dataset search.

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
| US-01 | [Infrastructure](US-01-infrastructure.md) | 3 | Docker stack with Weaviate, Vector MCP, Open WebUI, n8n |
| US-02 | [Knowledge Base](US-02-knowledge-base.md) | 2 | Expert knowledge for all LLM specialization methods |
| US-03 | [Agent Architecture](US-03-agent-architecture.md) | 4 | LangGraph agent with decision logic and recommendation reports |
| US-04 | [Integration](US-04-integration.md) | 1 | End-to-end testing and documentation |
| US-05 | [HuggingFace Search](US-05-huggingface-search.md) | 2 | Dataset search on HuggingFace Hub |

## Tasks

### US-01: Infrastructure

| ID | Title | Description |
|----|-------|-------------|
| T-01-1 | [Docker-Compose Foundation](T-01-1-docker-compose-foundation.md) | Weaviate, Vector MCP, MCP Inspector, Open WebUI |
| T-01-2 | [Stack Management Scripts](T-01-2-stack-management-scripts.md) | up.sh, down.sh |
| T-01-3 | [n8n Chatbot](T-01-3-n8n-chatbot.md) | n8n setup with dummy chatbot and Open WebUI connection |

### US-02: Knowledge Base

| ID | Title | Description |
|----|-------|-------------|
| T-02-1 | [Knowledge Ingestion Container](T-02-1-knowledge-ingestion-container.md) | Docker container for automatic collection setup and ingestion with hash-based change detection |
| T-02-2 | [Knowledge Documents](T-02-2-knowledge-documents.md) | Markdown documents for all LLM specialization methods and best practices |

### US-03: Agent Architecture

| ID | Title | Description |
|----|-------|-------------|
| T-03-1 | [LangGraph Agent](T-03-1-langgraph-agent.md) | Agent with Vector MCP integration |
| T-03-2 | [Agent Prompts & Starter Prompts](T-03-2-agent-prompts.md) | German prompts, structured interview, and Open WebUI starter prompts |
| T-03-3 | [Decision Logic & Recommendation Report](T-03-3-decision-logic.md) | Decision tree, multi-criteria evaluation, and structured report output |
| T-03-4 | [CI Pipeline](T-03-4-ci-pipeline.md) | CI pipeline for unit tests and linting |

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

## Total: 5 User Stories, 12 Tasks

