# User story

- tasks:
  - T-06-1
  - T-06-2
  - T-06-3
  - T-06-4
  - T-06-5
  - T-06-6

# Story

*"As a developer, I want a reproducible Ansible-based deployment for the Triton inference server and a configurable model selection in the Soofi Trainer, so that we can run local models on our GPU hardware and switch between local and cloud providers."*

# Description

The Soofi Trainer agent needs access to locally hosted LLM models via a Triton + vLLM inference server running on NVIDIA GPU hardware in the lab. The current [soofi-inference-server](https://mrk40.dfki.de/soofi/soofi-inference-server) project uses shell scripts for setup — these should be replaced with Ansible playbooks for reproducibility and OS independence.

The inference server runs on a separate machine from the Soofi Trainer stack. Triton exposes an OpenAI-compatible API (`/v1/chat/completions`) via vLLM, so the agent can connect directly without an additional proxy layer.

## Architecture

```
Soofi Trainer Stack              Lab Server (GPU)
+-----------------+              +------------------------+
| Agent           |  HTTPS/HTTP  | Triton + vLLM          |
| (LangGraph)     |------------->| /v1/chat/completions   |
|                 |              | (2x NVIDIA H200)       |
+-----------------+              +------------------------+
      |                                    ^
      | OPENAI_API_BASE                    |
      +-------- configured via .env -------+

Embedding: EMBEDDING_MODEL (openai:*, ollama:*, triton:*)
Chat:      CHAT_MODEL + OPENAI_API_BASE (OpenAI or Triton)
```

## Deployment Tool

Reuse the Ansible Docker image pattern from [soofi-cluster](https://mrk40.dfki.de/soofi/soofi-cluster) (`docker/Dockerfile.ansible`). The Ansible container runs locally and provisions the remote GPU server via SSH.

## Scope

- Network access & connectivity (Firewall, DNS, SSH) — T-06-1
- Ansible setup (Docker image, project structure, inventory) — T-06-2
- Server provisioning playbooks (OS, NVIDIA, Docker, Triton) — T-06-3
- Soofi Trainer integration (env vars, README, `.env`) — T-06-4
- Model evaluation & deployment on Triton (chat + embedding) — T-06-5
- Local inference with Ollama / LM Studio (dev PCs, 8 GB VRAM) — T-06-6
- No Kubernetes / Helm — that is a separate concern for the soofi-cluster project

## Integration with Soofi Trainer

The Soofi Trainer connects to models via environment variables:
- `OPENAI_API_BASE` — endpoint URL (OpenAI cloud or Triton server)
- `CHAT_MODEL` — chat/completion model name
- `EMBEDDING_MODEL` — embedding model (existing, already supports multiple providers)

Switching between cloud and local is a config change in `.env`, no code changes required.

# Acceptance Criteria

- [ ] Ansible playbooks can provision a fresh GPU server from scratch
- [ ] NVIDIA driver + CUDA + Container Toolkit installed via Ansible (OS-independent)
- [ ] Triton + vLLM running via Docker Compose on the GPU server
- [ ] Triton serves models via OpenAI-compatible API
- [ ] Soofi Trainer agent can connect to the inference server via `OPENAI_API_BASE`
- [ ] Chat model and embedding model are configurable via `.env`
- [ ] Switching between local (Triton) and cloud (OpenAI) requires only config changes
- [ ] README documents setup and configuration for all three modes (cloud, Triton, local)
- [ ] Local inference with Ollama / LM Studio works on dev PCs (8 GB VRAM)
- [ ] Deployment is reproducible — new server can be provisioned with same playbooks
