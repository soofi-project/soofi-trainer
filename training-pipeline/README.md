# Training Pipeline

Training infrastructure for the Soofi Trainer stack. Contains the Training Gateway MCP server and simulation containers for testing training workflows.

## Components

| Component | Path | Description |
|-----------|------|-------------|
| Training Gateway | `training-gateway/` | FastAPI + FastMCP server for job lifecycle management |
| Training Container | `training-container/` | Simulation container for development and testing |

See each component's README for details.

## Quick Start

### Run tests (no Docker)

```bash
cd training-gateway
pip install -e ".[dev]"
make test
```

### Run with Docker

```bash
# From soofi-trainer root:
docker compose up --build training-gateway

# Run a simulated training job:
docker compose run --rm dummy-training \
  --method lora \
  --dataset "sample/dataset.jsonl" \
  --base-model "meta-llama/Llama-3.1-8B" \
  --webhook-url "http://training-gateway:8000/webhooks" \
  --job-id "YOUR_JOB_ID" \
  --duration 30
```
