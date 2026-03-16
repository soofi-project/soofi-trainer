# Task

- user story: [US-08](US-08-training-pipeline.md)
- depends on: [T-08-1](T-08-1-training-gateway.md)

/label ~UserStory_US-08
/label ~Task
/label ~ToDo

# Description

**Dummy Training Containers**

Create Docker images that simulate the training process for each specialization method. Phase 1 uses a single parameterized base image; real implementations will follow later with method-specific images.

## Base Image

A Python-based Docker image that:
- Accepts method, dataset reference, base model, and gateway webhook URL as parameters
- Simulates the three training phases with configurable timing
- Sends webhook callbacks to the Training Gateway at each phase transition and progress update

```dockerfile
# Usage:
docker run soofi-pipeline/dummy \
  --method lora \
  --dataset /data/dataset.jsonl \
  --base-model meta-llama/Llama-3.1-8B \
  --webhook-url http://training-gateway:8000/webhooks \
  --duration 120  # total simulation time in seconds
```

## Phase Simulation

| Phase | Default Duration | Progress Events |
|-------|-----------------|-----------------|
| `data_preparation` | 20% of total | Every 10% — validation, formatting, splitting |
| `training` | 65% of total | Every 5% — epoch progress, simulated loss curve |
| `model_upload` | 15% of total | Every 20% — upload progress |

## Webhook Callbacks

The container sends HTTP POST requests to the gateway webhook URL:

1. **Phase start**: `POST /webhooks/job-phase-transition`
2. **Progress update**: `POST /webhooks/job-progress` (with percentage and optional metrics)
3. **Completion**: `POST /webhooks/job-completed` (with dummy model reference and metrics)
4. **Failure**: `POST /webhooks/job-failed` (configurable failure probability for testing)

## Method-Specific Behavior

Even as a dummy, each method should simulate realistic characteristics:

| Method | Simulated Behavior |
|--------|-------------------|
| SFT | Full training loop, higher resource usage reported |
| LoRA | Faster training, fewer parameters reported |
| QLoRA | Similar to LoRA with quantization step in data_preparation |
| RAG | No training phase — only data_preparation (indexing) and model_upload (index storage) |
| Distillation | Two-model setup reported (teacher + student) |

## Configurable Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--method` | Specialization method | required |
| `--dataset` | Dataset reference | required |
| `--base-model` | Base model name | required |
| `--webhook-url` | Gateway webhook base URL | required |
| `--duration` | Total simulation duration (seconds) | 120 |
| `--fail-probability` | Chance of simulated failure (0.0-1.0) | 0.0 |
| `--job-id` | Job ID (assigned by gateway) | required |

## Acceptance Criteria

- [ ] Base Docker image builds and runs successfully
- [ ] Container simulates all three phases (data_preparation, training, model_upload)
- [ ] Progress webhooks are sent to the gateway at regular intervals
- [ ] Phase transitions are reported via webhooks
- [ ] At least 3 methods have distinct simulation behavior (e.g. LoRA, SFT, RAG)
- [ ] RAG method correctly skips the training phase
- [ ] Duration is configurable for demo purposes
- [ ] Simulated failure mode works for error handling tests
- [ ] Container exits with appropriate exit code (0 = success, 1 = failure)
- [ ] Container logs show progress for debugging

# Branches

- feature/T-08-2-dummy-training-containers
