# User story

- tasks:
  - [T-08-1](T-08-1-training-gateway.md)
  - [T-08-2](T-08-2-dummy-training-containers.md)
  - [T-08-3](T-08-3-agent-training-flow.md)
  - [T-08-4](T-08-4-remote-deployment.md)
  - [T-08-5](T-08-5-training-progress-ui.md)
  - [T-08-6](T-08-6-aas-submodel-push.md)
  - [T-08-7](T-08-7-aas-base-model-nameplates.md)

/label ~UserStory
/milestone %ProductBacklog

# Story

*"As a user, I want the Soofi agent to trigger a training pipeline for the recommended specialization method using my provided datasets, so that I can see the full process from recommendation to model training without manual intervention."*

# Description

After the agent has completed the analysis ([US-03](US-03-agent-architecture.md)) and the user has confirmed the recommended specialization method and selected training datasets ([US-04](US-04-dataset-search.md)), the system should be able to trigger a training pipeline. In Phase 1, this is a **dummy pipeline** that simulates the training process with realistic phases and progress reporting.

A **Training Gateway** service acts as a mediator between the agent and the remote training infrastructure. It exposes MCP tools so the agent can start, monitor, and cancel training jobs — fitting seamlessly into the existing MCP-based architecture. The gateway abstracts whether the training containers run on Docker Compose, Kubernetes, or SLURM clusters.

Each specialization method (LoRA, SFT, QLoRA, RAG, etc.) has its own Docker image containing the method-specific dependencies and training logic. In Phase 1, these containers simulate the training process with realistic timing and progress callbacks.

## Architecture

```
Soofi Trainer Stack                          Remote Infrastructure (Docker/K8s)
+-------------------+     +-----------------+     +-------------------------+
|   Agent           |---->| Training        |---->| lora-pipeline           |
|   (LangGraph)     |<-MCP| Gateway         |<-WH | sft-pipeline            |
+-------------------+     | (FastAPI + MCP) |     | qlora-pipeline          |
      |                   | - Job State DB  |     | rag-pipeline            |
      v                   | - Webhook Recv  |     | distillation-pipeline   |
+-------------------+     +-----------------+     +-------------------------+
| A2UI / Open WebUI |           |
| (Progress View)   |     persistent state
+-------------------+     (SQLite / PostgreSQL)
```

## Communication Flow

1. **Agent → Gateway**: MCP tools (`start_training_job`, `get_job_status`, `cancel_job`)
2. **Gateway → Remote**: REST API to start/stop containers on remote infrastructure
3. **Remote → Gateway**: Webhook callbacks for phase transitions and progress updates
4. **Gateway → Agent → User**: Agent polls status via MCP and presents progress to user

## Phase Model

Every training job progresses through defined phases:

| Phase | Description | Typical Progress Events |
|-------|-------------|------------------------|
| `data_preparation` | Validation, formatting, train/eval split | File count, validation results |
| `training` | Model training with epochs/steps | Epoch, loss, step progress |
| `model_upload` | Push trained model to registry | Upload progress |

## Specialization Methods (Docker Images)

| Method | Image | Notes |
|--------|-------|-------|
| Supervised Fine-Tuning (SFT) | `soofi-pipeline/sft` | Full fine-tuning |
| LoRA | `soofi-pipeline/lora` | Low-rank adaptation |
| QLoRA | `soofi-pipeline/qlora` | Quantized LoRA |
| RAG | `soofi-pipeline/rag` | Index building, no model training |
| Knowledge Distillation | `soofi-pipeline/distillation` | Teacher → Student |
| Continued Pretraining | `soofi-pipeline/cpt` | Domain adaptation |
| Instruction Tuning | `soofi-pipeline/instruction` | Chat/assistant format |
| DPO | `soofi-pipeline/dpo` | Direct preference optimization |
| RLHF | `soofi-pipeline/rlhf` | Reinforcement learning from human feedback |

Phase 1 (dummy) uses a single base image parameterized by method. Real implementations will use dedicated images.

## Dependencies

- **[US-03](US-03-agent-architecture.md)**: Agent recommendation provides the method and parameters
- **[US-04](US-04-dataset-search.md)**: Dataset search provides the training data references
- **[US-06](US-06-inference-server.md)**: Inference server patterns (Ansible, remote deployment) are reused
- **[US-07](US-07-voice-agent-ui.md)** (optional): A2UI frontend for rich progress visualization

# Acceptance Criteria

- [ ] Training Gateway runs as a service in the Soofi Trainer Docker Compose stack
- [ ] Agent can start a training job via MCP tool (`start_training_job`)
- [ ] Agent can query job status via MCP tool (`get_job_status`)
- [ ] Agent can cancel a running job via MCP tool (`cancel_job`)
- [ ] Training containers run on separate remote infrastructure (Docker or Kubernetes)
- [ ] Job progress is tracked in phases (data_preparation → training → model_upload)
- [ ] Each phase reports percentage progress
- [ ] Job state persists across agent conversations (user can ask for status later)
- [ ] Dummy training containers simulate realistic training with configurable duration
- [ ] At least 3 specialization methods are available as dummy containers (e.g. LoRA, SFT, RAG)
- [ ] User sees training progress in the UI (phases + percentages)
- [ ] Gateway abstracts infrastructure — switching Docker/K8s requires no agent changes
