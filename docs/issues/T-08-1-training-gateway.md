# Task

- user story: [US-08](US-08-training-pipeline.md)

/label ~UserStory_US-08
/label ~Task
/label ~ToDo

# Description

**Training Gateway MCP Server**

Create a FastAPI service that exposes MCP tools for training job management. The gateway is the single point of contact between the Soofi agent and the remote training infrastructure.

## MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `start_training_job` | Submit a new training job | `method`, `dataset_ref`, `base_model`, `config` (optional) |
| `get_job_status` | Query current status of a job | `job_id` |
| `list_jobs` | List all jobs (with optional status filter) | `status` (optional) |
| `cancel_job` | Cancel a running or queued job | `job_id` |

## Job State Model

```
Job {
  id: string (UUID)
  method: string (lora, sft, qlora, rag, ...)
  dataset_ref: string
  base_model: string
  status: queued | running | completed | failed | cancelled
  current_phase: string
  phases: [
    { name: string, status: string, progress: int (0-100), started_at, completed_at }
  ]
  created_at: datetime
  updated_at: datetime
  error: string (optional)
  result: { model_ref: string, metrics: object } (optional)
}
```

## Webhook Receiver

The gateway exposes a webhook endpoint that training containers call to report progress:

```
POST /webhooks/job-progress
{
  "job_id": "abc-123",
  "phase": "training",
  "progress": 42,
  "metrics": { "loss": 0.23, "epoch": 2 }  // optional
}

POST /webhooks/job-phase-transition
{
  "job_id": "abc-123",
  "from_phase": "data_preparation",
  "to_phase": "training"
}

POST /webhooks/job-completed
{
  "job_id": "abc-123",
  "result": { "model_ref": "registry/model:v1", "metrics": {...} }
}

POST /webhooks/job-failed
{
  "job_id": "abc-123",
  "error": "OOM during training at epoch 3"
}
```

## Persistence

- SQLite for Phase 1 (single-file, no extra infrastructure)
- Job state survives gateway restarts
- Docker volume for the database file

## Docker Compose Integration

- Service name: `training-gateway`
- Internal network access to training infrastructure
- MCP endpoint accessible by the agent

## Acceptance Criteria

- [ ] FastAPI service starts as `training-gateway` in docker-compose
- [ ] MCP tools `start_training_job`, `get_job_status`, `list_jobs`, `cancel_job` are functional
- [ ] Webhook endpoints receive and process progress callbacks from training containers
- [ ] Job state is persisted in SQLite and survives container restarts
- [ ] Job state includes phases with individual progress percentages
- [ ] MCP tools are discoverable via MCP Inspector
- [ ] Gateway validates incoming webhook payloads
- [ ] API documented (OpenAPI / Swagger)

# Branches

- feature/T-08-1-training-gateway
