# Task

- user story: [US-08](US-08-training-pipeline.md)
- depends on: [T-08-1](T-08-1-training-gateway.md), [T-03-1](T-03-1-langgraph-agent.md), [T-03-3](T-03-3-decision-logic.md)

/label ~UserStory_US-08
/label ~Task
/label ~ToDo

# Description

**Agent Training Flow**

Integrate the training pipeline into the LangGraph agent's conversation flow. After the agent has recommended a specialization method ([US-03](US-03-agent-architecture.md)) and the user has confirmed, the agent offers to start a training job and monitors its progress.

## Conversation Flow

```
Agent: "Based on your use case, I recommend LoRA fine-tuning with
        the dataset 'german-qa-pairs' on Llama-3.1-8B. Shall I
        start the training?"

User:  "Yes, start the training."

Agent: [calls start_training_job via MCP]
       "Training job started (Job ID: abc-123). I'll keep you
        updated on the progress."

       "Phase 1/3: Data Preparation — 45% complete..."
       "Phase 1/3: Data Preparation — complete ✓"
       "Phase 2/3: Model Training — 12% (Epoch 1/5, Loss: 2.34)..."
       ...
       "Training complete! The model has been uploaded to the
        registry. Here's the summary: ..."

--- or in a later conversation ---

User:  "What's the status of my training?"

Agent: [calls get_job_status via MCP]
       "Your LoRA training (Job abc-123) is currently in Phase 2/3
        (Model Training) at 67%. Estimated time remaining: ~8 min."
```

## Agent Integration Points

### New LangGraph Node: `training_manager`

- Triggered after recommendation confirmation
- Uses MCP tools: `start_training_job`, `get_job_status`, `cancel_job`
- Handles job lifecycle within the conversation

### State Extensions

Add to the agent's conversation state:
- `active_job_id`: Currently tracked training job
- `training_method`: Selected specialization method
- `training_status`: Last known job status

### Decision Points

| Trigger | Agent Action |
|---------|-------------|
| User confirms recommendation | Offer to start training |
| User says "start training" | Call `start_training_job` |
| User asks about progress | Call `get_job_status` |
| User wants to cancel | Call `cancel_job` with confirmation |
| Job completes | Present results summary |
| Job fails | Present error and suggest next steps |

## MCP Tool Registration

Register the Training Gateway's MCP tools in the agent's tool configuration, alongside existing tools (Vector MCP, HuggingFace MCP, etc.).

## Progress Reporting

The agent should present progress in a user-friendly format:
- Phase name and number (e.g. "Phase 2/3: Model Training")
- Percentage within the current phase
- Relevant metrics when available (loss, epoch)
- Estimated time remaining (based on elapsed time and progress)

## Acceptance Criteria

- [ ] Agent offers training after recommendation confirmation
- [ ] Agent starts training jobs via `start_training_job` MCP tool
- [ ] Agent reports progress with phases and percentages
- [ ] Agent handles job completion with a results summary
- [ ] Agent handles job failure with error message and suggestions
- [ ] Agent supports cancellation with user confirmation
- [ ] User can query training status in a new conversation
- [ ] LangGraph state includes training job tracking
- [ ] Training MCP tools are registered alongside existing tools

# Branches

- feature/T-08-3-agent-training-flow
