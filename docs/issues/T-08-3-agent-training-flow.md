# Task

- user story: [US-08](US-08-training-pipeline.md)
- depends on: [T-08-1](T-08-1-training-gateway.md), [T-07-6](T-07-6-interaction-agent.md)

/label ~UserStory_US-08
/label ~Task
/label ~ToDo

# Description

**Training Agent + Agent Training Flow**

Introduce a dedicated **Training Agent** — a new A2A specialist that handles training job
initiation and conversational queries about job status. The Interaction Agent delegates to it
via A2A, mirroring the existing Advisor pattern.

Training jobs run for minutes to hours. The agent flow is therefore **fire-and-render**: start
the job, hand back a job ID, and let the frontend component ([T-08-5](T-08-5-training-progress-ui.md))
own the live progress display independently.

## Architecture

```
[Browser] ──AG-UI──▶ [Interaction Agent] ──A2A──▶ [Advisor]         ──MCP──▶ [Weaviate]
                                          ──A2A──▶ [Training Agent]  ──MCP──▶ [Training Gateway]
```

## New Service: Training Agent (`training-agent/`)

A LangGraph ReAct agent served via FastAPI (same stack as `advisor/`).

### Responsibilities

- Receives a training task from the Interaction Agent via A2A
- Calls `start_training_job` on the Training Gateway via MCP, returns the job ID
- Handles conversational status queries ("what's the status of my training?") by calling
  `get_job_status` and formatting a human-readable summary
- Handles cancellation requests: calls `cancel_training_job` and confirms

The Training Agent does **not** maintain a long-lived polling loop. Live progress display is
handled by the `<soofi-training-progress>` frontend component ([T-08-5](T-08-5-training-progress-ui.md)).

## Interaction Agent Changes

Add `ask_training_agent_tool` alongside the existing `ask_advisor_tool`:

```python
@tool
async def ask_training_agent_tool(request: str) -> AsyncGenerator[str, None]:
    """Delegate a training request to the Training Agent via A2A."""
    async for chunk in stream_training_agent(request):
        yield chunk
```

After the Training Agent confirms that a job has started, the IA sends a UI component message
to the frontend to render the training progress view:

```python
# After job start confirmed — push <soofi-training-progress> to frontend
await writer({"type": "custom", "component": "soofi-training-progress"})
```

The component then fetches job status independently ([T-08-5](T-08-5-training-progress-ui.md)).

## Conversation Flow

```
User:  "Let's start the LoRA training we discussed."

IA:    [delegates to Training Agent via A2A]
       "Training job started (Job ID: abc-123).
        You can track the progress below."
       [renders <soofi-training-progress> component in UI]

--- status query (Training Agent fetches via MCP, formats response) ---

User:  "What's the status of my training?"

IA:    [delegates to Training Agent via A2A]
       "Your LoRA training (abc-123) is in Phase 2/3 — Model Training
        at 67%. Estimated time remaining: ~8 min."

--- cancel ---

User:  "Please cancel the training."
IA:    "Are you sure you want to cancel job abc-123?"
User:  "Yes."
IA:    [Training Agent calls cancel_training_job]
       "Training job abc-123 has been cancelled."
```

## docker-compose.yml

Add `training-agent` service (analogous to `advisor`):

```yaml
training-agent:
  build: ./training-agent
  container_name: training-agent
  restart: unless-stopped
  env_file:
    - .env
    - ${ENV_SECRETS_FILE}
  environment:
    - TRAINING_GATEWAY_MCP_URL=http://training-gateway:8000/mcp
    - TRAINING_AGENT_NAME=soofi-training-agent
  networks:
    - soofi-network
  depends_on:
    training-gateway:
      condition: service_healthy
  healthcheck:
    test: ["CMD-SHELL", "python -c \"import socket; s=socket.create_connection(('localhost',8000),2); s.close()\""]
    interval: 10s
    timeout: 5s
    retries: 5
```

The `interaction-agent` service gains `TRAINING_AGENT_URL=http://training-agent:8000`.

## Acceptance Criteria

- [ ] `training-agent/` service exists and starts as part of the docker-compose stack
- [ ] Training Agent exposes an A2A endpoint reachable by the Interaction Agent
- [ ] Interaction Agent delegates training requests to Training Agent via `ask_training_agent_tool`
- [ ] Training Agent calls `start_training_job` on the Training Gateway via MCP
- [ ] Training Agent handles "what's the status?" queries via `get_job_status`
- [ ] Training Agent handles cancellation via `cancel_training_job`
- [ ] After job start, IA renders `<soofi-training-progress>` component in the frontend
- [ ] Interaction Agent does NOT call Training Gateway MCP tools directly

# Branches

- feature/T-08-3-agent-training-flow
