# Dummy Training Container

Simulates the training process for each specialization method by progressing through phases and reporting progress via webhooks to the Training Gateway.

## How It Works

```
┌──────────────────────────┐         Webhooks          ┌───────────────────┐
│  Dummy Training Container│ ───────────────────────── │ Training Gateway  │
│                          │  POST /webhooks/           │   (FastAPI +      │
│  1. data_preparation     │    job-progress            │    FastMCP)       │
│  2. training             │    job-phase-transition    │                   │
│  3. model_upload         │    job-completed           │  ┌─────────────┐  │
│                          │    job-failed              │  │  SQLite DB   │  │
└──────────────────────────┘                           │  └─────────────┘  │
                                                       └───────────────────┘
```

1. The Training Gateway creates a job and passes its `job_id` to this container
2. The container simulates each phase, sleeping proportionally to `--duration`
3. At each progress step, it sends a `POST /webhooks/job-progress` to the gateway
4. At phase boundaries, it sends `POST /webhooks/job-phase-transition`
5. On completion: `POST /webhooks/job-completed` with a dummy model reference
6. On failure: `POST /webhooks/job-failed` with an error message

## Phase Simulation

| Phase | Duration Share | Progress Step | Description |
|-------|---------------|---------------|-------------|
| `data_preparation` | 20% | Every 10% | Validation, formatting, splitting |
| `training` | 65% | Every 5% | Epoch progress, simulated loss curve |
| `model_upload` | 15% | Every 20% | Upload progress |

RAG jobs skip the `training` phase entirely (only `data_preparation` + `model_upload`).

## Method-Specific Behavior

| Method | Simulated Characteristics |
|--------|--------------------------|
| SFT | Full 7B params, 40 GB GPU memory |
| LoRA | 18.7M trainable params, rank 16, learning rate decay |
| QLoRA | Like LoRA + quantization step in data_preparation |
| RAG | No training phase, HNSW index building only |
| Distillation | Teacher (70B) + student (8B) setup |
| DPO | 7B params, beta=0.1 |
| RLHF | 7B params, PPO with 4 epochs |

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--method` | yes | — | Training method (`sft`, `lora`, `qlora`, `rag`, `distillation`, `cpt`, `instruction`, `dpo`, `rlhf`) |
| `--dataset` | yes | — | Dataset reference path |
| `--base-model` | yes | — | Base model name |
| `--webhook-url` | yes | — | Gateway webhook base URL (e.g. `http://training-gateway:8000/webhooks`) |
| `--job-id` | yes | — | Job ID assigned by the gateway |
| `--duration` | no | 120 | Total simulation duration in seconds |
| `--fail-probability` | no | 0.0 | Chance of simulated failure (0.0–1.0) |

## Build & Run

### As part of the stack

The container uses a Docker Compose profile and does not start automatically:

```bash
# Build the image
docker compose build dummy-training

# Run a simulation (requires a running training-gateway with a valid job_id)
docker compose run --rm dummy-training \
  --method lora \
  --dataset /data/dataset.jsonl \
  --base-model meta-llama/Llama-3.1-8B \
  --webhook-url http://training-gateway:8000/webhooks \
  --job-id YOUR_JOB_ID \
  --duration 60
```

### Standalone

```bash
cd dummy-training-container
docker build -t soofi-pipeline/dummy .
docker run --rm --network soofi-trainer_soofi-network soofi-pipeline/dummy \
  --method lora \
  --dataset /data/dataset.jsonl \
  --base-model meta-llama/Llama-3.1-8B \
  --webhook-url http://training-gateway:8000/webhooks \
  --job-id YOUR_JOB_ID \
  --duration 60
```

## Testing Scenarios

```bash
# Normal LoRA run (30 seconds)
docker compose run --rm dummy-training \
  --method lora --dataset /data/d.jsonl --base-model llama-3.1-8B \
  --webhook-url http://training-gateway:8000/webhooks \
  --job-id JOB_ID --duration 30

# RAG (skips training phase)
docker compose run --rm dummy-training \
  --method rag --dataset /data/docs/ --base-model n/a \
  --webhook-url http://training-gateway:8000/webhooks \
  --job-id JOB_ID --duration 15

# Guaranteed failure (for error handling tests)
docker compose run --rm dummy-training \
  --method sft --dataset /data/d.jsonl --base-model llama-3.1-8B \
  --webhook-url http://training-gateway:8000/webhooks \
  --job-id JOB_ID --duration 10 --fail-probability 1.0
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Simulation completed successfully |
| 1 | Simulation failed (simulated or real error) |
