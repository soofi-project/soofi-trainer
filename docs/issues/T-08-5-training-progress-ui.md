# Task

- user story: [US-08](US-08-training-pipeline.md)
- depends on: [T-08-1](T-08-1-training-gateway.md), [T-08-3](T-08-3-agent-training-flow.md)

/label ~UserStory_US-08
/label ~Task
/label ~ToDo

# Description

**Training Progress UI**

Visualize training job progress for the user. Supports two modes: text-based progress in Open WebUI (baseline) and rich visual progress via A2UI (if [US-07](US-07-voice-agent-ui.md) is available).

## Mode 1: Open WebUI (Text-Based)

The agent formats training progress as structured text messages in the chat:

```
🔄 Training Job: abc-123
Method: LoRA | Base Model: Llama-3.1-8B

Phase 1/3: Data Preparation ............. ✅ complete
Phase 2/3: Model Training ............... ⏳ 67%
  ├─ Epoch: 3/5
  ├─ Loss: 0.42
  └─ ETA: ~4 min
Phase 3/3: Model Upload ................. ⏸ pending
```

- Works immediately with the existing Open WebUI setup
- Agent constructs the message from `get_job_status` response
- Periodic updates as new messages in the chat

## Mode 2: A2UI (Rich Visual — depends on US-07)

If the A2UI frontend ([T-07-1](T-07-1-a2ui-frontend.md)) is available, the Interaction Agent ([T-07-6](T-07-6-interaction-agent.md)) renders training progress as dynamic A2UI components:

### A2UI Component: `soofi-training-progress`

```json
{
  "type": "custom",
  "component": "soofi-training-progress",
  "props": {
    "jobId": "abc-123",
    "method": "LoRA",
    "baseModel": "Llama-3.1-8B",
    "phases": [
      { "name": "Data Preparation", "status": "completed", "progress": 100 },
      { "name": "Model Training", "status": "running", "progress": 67,
        "metrics": { "epoch": "3/5", "loss": 0.42 } },
      { "name": "Model Upload", "status": "pending", "progress": 0 }
    ],
    "eta": "~4 min"
  }
}
```

### Visual Design

- Step indicator (horizontal or vertical) showing all phases
- Progress bar per active phase with percentage
- Metrics panel (loss curve, epoch, ETA) for training phase
- Status badges: pending (gray), running (blue/animated), completed (green), failed (red)
- Cancel button with confirmation dialog

### Real-Time Updates

- Interaction Agent receives status updates via SSE from the Training Gateway
- Pushes A2UI component updates to the frontend
- Progress bar and metrics animate smoothly between updates

## Agent Prompt Extensions

Add prompt instructions for the agent to format training progress appropriately:
- Use structured text format in Open WebUI mode
- Send A2UI components in A2UI mode
- Include relevant metrics (loss, epoch) when available
- Provide ETA estimates

## Acceptance Criteria

- [ ] Text-based progress display works in Open WebUI chat
- [ ] Progress shows phase names, status, and percentages
- [ ] Training metrics (loss, epoch) are displayed when available
- [ ] Completion and failure states are clearly communicated
- [ ] A2UI `soofi-training-progress` component renders phases and progress (when US-07 available)
- [ ] Real-time updates work without page refresh (A2UI mode)
- [ ] Cancel button available in both modes
- [ ] Agent formats progress appropriately based on available frontend

# Branches

- feature/T-08-5-training-progress-ui
