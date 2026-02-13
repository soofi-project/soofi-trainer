# Training Gateway

MCP server for training job management in the Soofi Trainer stack. Acts as mediator between the LangGraph agent and remote training infrastructure (Docker/Kubernetes).

## Communication Flow

```
                   Soofi Trainer Stack
┌──────────────┐       MCP tools        ┌───────────────────┐
│    Agent     │ ──────────────────────▶ │ Training Gateway  │
│ (LangGraph)  │  start_training_job     │   (FastAPI +      │
│              │  get_job_status          │    FastMCP)        │
│              │  list_training_jobs      │                   │
│              │  cancel_training_job     │  ┌─────────────┐  │
└──────────────┘                         │  │  SQLite DB   │  │
                                         │  │  (job state) │  │
                                         │  └─────────────┘  │
                                         └────────┬──────────┘
                                                  │
                              REST (start)        │       Webhooks (progress)
                        ┌─────────────────────────┼──────────────────────┐
                        ▼                         │                      │
               Remote Infrastructure              │                      │
        ┌──────────────────────┐                  │                      │
        │  Training Container  │ ─── POST /webhooks/job-progress ────────┘
        │  (lora, sft, rag...) │ ─── POST /webhooks/job-phase-transition
        │                      │ ─── POST /webhooks/job-completed
        │                      │ ─── POST /webhooks/job-failed
        └──────────────────────┘
```

### Sequence

1. **Agent** calls `start_training_job` via MCP → Gateway creates job record, returns `job_id`
2. **Gateway** starts a training container on remote infrastructure (T-08-4, not yet implemented)
3. **Training container** sends webhook callbacks to the gateway as it progresses:
   - `job-progress` — phase percentage updates (e.g. "training: 42%")
   - `job-phase-transition` — phase changes (e.g. data_preparation → training)
   - `job-completed` / `job-failed` — terminal state
4. **Agent** polls `get_job_status` via MCP and presents progress to the user
5. **User** can cancel via `cancel_training_job`

### Phase Model

Every training job progresses through defined phases:

```
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ data_preparation │──▶│    training       │──▶│  model_upload     │
│     0–100%       │   │     0–100%       │   │     0–100%       │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```

RAG jobs skip the `training` phase (index building only).

## Endpoints

| Path | Protocol | Description |
|------|----------|-------------|
| `/mcp` | MCP (Streamable HTTP) | MCP tools for agent communication |
| `/webhooks/job-progress` | REST POST | Progress update from training container |
| `/webhooks/job-phase-transition` | REST POST | Phase transition notification |
| `/webhooks/job-completed` | REST POST | Job completion notification |
| `/webhooks/job-failed` | REST POST | Job failure notification |
| `/health` | REST GET | Health check |
| `/docs` | HTTP GET | Swagger UI (OpenAPI documentation) |

## MCP Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `start_training_job` | `method`, `dataset_ref`, `base_model`, `config` | Start a new training job |
| `get_job_status` | `job_id` | Get full job state with phases and progress |
| `list_training_jobs` | `status` (optional) | List all jobs, optionally filtered |
| `cancel_training_job` | `job_id` | Cancel a running or queued job |

### Supported Methods

`sft`, `lora`, `qlora`, `rag`, `distillation`, `cpt`, `instruction`, `dpo`, `rlhf`

## Build & Run

### As part of the stack

```bash
# From the soofi-trainer root:
docker compose up --build training-gateway
```

### Standalone

```bash
cd training-pipeline/training-gateway
docker build -t training-gateway .
docker run -p 8000:8000 -v training_data:/data training-gateway
```

### Local development

```bash
cd training-pipeline/training-gateway
pip install -e ".[dev]"
TRAINING_DB_PATH=./training.db python src/training_gateway/server.py
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port |
| `TRAINING_DB_PATH` | `/data/training.db` | SQLite database file path |

## Project Structure

```
training-gateway/
├── pyproject.toml
├── Makefile
├── Dockerfile
├── README.md
├── src/training_gateway/
│   ├── __init__.py
│   ├── server.py        # FastAPI app + FastMCP mount + uvicorn
│   ├── mcp_tools.py     # MCP tool definitions
│   ├── webhooks.py      # Webhook REST endpoints
│   ├── models.py        # Pydantic models and enums
│   └── db.py            # SQLite persistence layer
└── tests/
    ├── conftest.py      # Shared fixtures (temp DB, async client)
    ├── unit/            # Models, DB layer
    ├── integration/     # Webhook endpoints, MCP tools
    └── e2e/             # Full workflow tests
```

## Testing

Tests run without Docker using pytest, temporary SQLite databases, and FastAPI TestClient.

```bash
cd training-pipeline/training-gateway
pip install -e ".[dev]"

make test              # All tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-e2e          # E2E workflow tests only
make test-cov          # With coverage report
```

### E2E Test Scenarios

| Test | Description |
|------|-------------|
| `test_lora_success` | Full 3-phase LoRA flow → completed |
| `test_rag_skip_training` | RAG with 2 phases (no training) → completed |
| `test_sft_failure_during_training` | Partial training → failure at 45% |

## Testing with curl

```bash
# Health check
curl http://localhost:8000/health

# Send a progress update (requires a valid job_id)
curl -X POST http://localhost:8000/webhooks/job-progress \
  -H "Content-Type: application/json" \
  -d '{"job_id": "YOUR_JOB_ID", "phase": "training", "progress": 42}'

# Mark a job as completed
curl -X POST http://localhost:8000/webhooks/job-completed \
  -H "Content-Type: application/json" \
  -d '{"job_id": "YOUR_JOB_ID", "result": {"model_ref": "registry/model:v1"}}'
```

## Testing with MCP Inspector

1. Start the stack: `docker compose up -d`
2. Open MCP Inspector: http://localhost:6274
3. Connect to: `http://training-gateway:8000/mcp/`
4. Use the tools panel to call `start_training_job`, `get_job_status`, etc.
