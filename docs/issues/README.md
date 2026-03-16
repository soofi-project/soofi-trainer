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
                    ┌────┴────┐
                    ▼         ▼
             ┌───────────┐ ┌───────────┐
             │HuggingFace│ │ Eclipse   │
             │MCP Server │ │ Dataspace │
             │(Datasets) │ │MCP Server │
             └───────────┘ └───────────┘
```

## User Stories

| ID | Title | Tasks | Description |
|----|-------|-------|-------------|
| US-01 | [Infrastructure](US-01-infrastructure.md) | 3 | Docker stack with Weaviate, Vector MCP, Open WebUI, n8n |
| US-02 | [Knowledge Base](US-02-knowledge-base.md) | 2 | Expert knowledge for all LLM specialization methods |
| US-03 | [Agent Architecture](US-03-agent-architecture.md) | 4 | LangGraph agent with decision logic and recommendation reports |
| US-04 | [Dataset Search](US-04-dataset-search.md) | 3 | Dataset search via separate MCP servers (HuggingFace, Eclipse Dataspace) |
| US-05 | [Integration](US-05-integration.md) | 1 | End-to-end testing and documentation |
| US-06 | [Inference Server](US-06-inference-server.md) | 6 | Ansible-based Triton + vLLM deployment on H200 GPU hardware |
| US-07 | [Voice Agent UI](US-07-voice-agent-ui.md) | 7 | A2UI + Lit frontend with voice pipeline (cloud ✅, H200 pending), push-to-talk, A2A orchestration |
| US-08 | [Training Pipeline](US-08-training-pipeline.md) | 5 | Dummy training pipeline with gateway, remote containers, and progress tracking |
| US-09 | [Agent Observability](US-09-agent-observability.md) | 3 | Real-time agent flow visualization, LLM tracing via Langfuse, RAG transparency panel |

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

### US-04: Dataset Search

| ID | Title | Description |
|----|-------|-------------|
| T-04-1 | [HuggingFace MCP Server](T-04-1-huggingface-mcp.md) | Separate MCP server for HuggingFace dataset search |
| T-04-2 | [Eclipse Dataspace MCP Server](T-04-2-eclipse-dataspace-mcp.md) | Separate MCP server for Eclipse Dataspace dataset search |
| T-04-3 | [Agent Integration](T-04-3-agent-integration.md) | Agent integration with all dataset search sources |

### US-05: Integration

| ID | Title | Description |
|----|-------|-------------|
| T-05-1 | [End-to-End Test](T-05-1-end-to-end-test.md) | End-to-end test and documentation |

### US-06: Inference Server

| ID | Title | Description |
|----|-------|-------------|
| T-06-1 | [Network Access](T-06-1-network-access.md) | Firewall, DNS, SSH connectivity |
| T-06-2 | [Ansible Setup](T-06-2-ansible-setup.md) | Docker image, project structure, inventory |
| T-06-3 | [Server Provisioning](T-06-3-server-provisioning.md) | OS, NVIDIA, Docker, Triton playbooks |
| T-06-4 | [Trainer Integration](T-06-4-trainer-integration.md) | Env vars, README, .env configuration |
| T-06-5 | [Model Selection](T-06-5-model-selection.md) | Model evaluation & deployment on Triton |
| T-06-6 | [Local Inference](T-06-6-local-inference.md) | Ollama / LM Studio on dev PCs |

### US-07: Voice Agent UI

| ID | Title | Description |
|----|-------|-------------|
| T-07-1 | [A2UI + Lit Frontend](T-07-1-a2ui-frontend.md) | A2UI + Lit frontend scaffold |
| T-07-2 | [Custom Components](T-07-2-custom-components.md) | Custom components & theming |
| T-07-3 | [Voice Pipeline (Cloud)](T-07-3-voice-local.md) | STT + TTS via OpenAI APIs, push-to-talk, stream delegation, sentence-buffer TTS ✅ |
| T-07-4 | [Voice on H200](T-07-4-voice-h200.md) | Local STT (faster-whisper-server) + TTS (Piper) on H200, Ansible deployment |
| T-07-5 | [Dashboard Embedding](T-07-5-dashboard-embedding.md) | Dashboard embedding (exploration) |
| T-07-6 | [Interaction Agent](T-07-6-interaction-agent.md) | Interaction Agent (A2A orchestrator) |
| T-07-7 | [Async A2A Status Push](T-07-7-a2a-status-push.md) | Advisor pushes intermediate status + speech intro before RAG results arrive |

### US-08: Training Pipeline

| ID | Title | Description |
|----|-------|-------------|
| T-08-1 | [Training Gateway](T-08-1-training-gateway.md) | Training Gateway MCP Server (FastAPI, job state, webhooks) |
| T-08-2 | [Dummy Training Containers](T-08-2-dummy-training-containers.md) | Parameterized Docker images simulating training per method |
| T-08-3 | [Agent Training Flow](T-08-3-agent-training-flow.md) | LangGraph integration for training lifecycle |
| T-08-4 | [Remote Deployment](T-08-4-remote-deployment.md) | Container orchestration on remote Docker/K8s |
| T-08-5 | [Training Progress UI](T-08-5-training-progress-ui.md) | Progress visualization (text + A2UI) |

## Recommended Order

1. **US-01** - Infrastructure (must be first)
2. **US-02** - Knowledge Base (can start parallel with US-03)
3. **US-03** - Agent Architecture
4. **US-04** - Dataset Search (can start parallel with US-03)
5. **US-05** - Integration & Testing
6. **US-06** - Inference Server (can start parallel with US-03)
7. **US-07** - Voice Agent UI (after US-03)
8. **US-08** - Training Pipeline (after US-03 + US-04)

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

### US-09: Agent Observability

| ID | Title | Description |
|----|-------|-------------|
| T-09-1 | [Langfuse](T-09-1-langfuse.md) | Local Langfuse Docker service + LangGraph callback integration |
| T-09-2 | [Agent Flow UI](T-09-2-agent-flow-ui.md) | Animated SVG architecture diagram in A2UI frontend, driven by TOOL_CALL events |
| T-09-3 | [RAG Transparency Panel](T-09-3-rag-transparency.md) | Source document preview + reranker relevance scores during Advisor retrieval |

## Total: 9 User Stories, 34 Tasks

