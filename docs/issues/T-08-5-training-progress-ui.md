# Task

- user story: [US-08](US-08-training-pipeline.md)
- depends on: [T-08-1](T-08-1-training-gateway.md), [T-08-3](T-08-3-agent-training-flow.md), [T-07-1](T-07-1-a2ui-frontend.md)

/label ~UserStory_US-08
/label ~Task
/label ~ToDo

# Description

**Training Progress UI**

A `<soofi-training-progress>` Lit Web Component that displays all training jobs and their live
progress. The component operates independently of the ongoing chat conversation — the user can
start a job, come back minutes later, and still see the current state.

The component appears in the A2UI frontend when the Interaction Agent sends a custom component
message after a training job is started ([T-08-3](T-08-3-agent-training-flow.md)).

## Data Source

The Training Gateway exposes a lightweight REST status API (new, in addition to the existing
MCP endpoint) that the frontend component can poll directly:

```
GET /jobs          → list of all jobs with current status
GET /jobs/{id}     → single job details (phases, metrics, progress)
```

The component polls every 3 s while a job is active, stops when all jobs reach a terminal state.
No long-lived SSE connection needed — training jobs run for minutes to hours.

The `TRAINING_GATEWAY_PORT` is already configurable in `.env`. The soofi-ui Dockerfile receives
the URL as a Vite build arg (`VITE_TRAINING_GATEWAY_URL`).

## Component: `<soofi-training-progress>`

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Training Jobs                                        [hide] │
├─────────────────────────────────────────────────────────────┤
│  abc-123  LoRA · Llama-3.1-8B                 ⏳ running    │
│                                                              │
│  ① Data Preparation  ──────────────────────────────  ✅     │
│  ② Model Training    ████████████░░░░░░░░░░░░░░░░░  67%    │
│     Epoch 3/5 · Loss 0.42 · ETA ~4 min                      │
│  ③ Model Upload      ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  —      │
│                                              [Cancel]        │
├─────────────────────────────────────────────────────────────┤
│  def-456  QLoRA · Mistral-7B                  ✅ complete   │
│  Completed 14:32 · Duration 23 min                          │
└─────────────────────────────────────────────────────────────┘
```

- All jobs are listed, newest first
- Completed/failed jobs are shown collapsed by default
- Active job is expanded with phase progress bars and metrics

### Phase States

| State | Visual |
|-------|--------|
| `pending` | Grey, empty bar |
| `running` | Blue, animated progress bar |
| `completed` | Green checkmark |
| `failed` | Red ✗ with error message |

### Cancel Button

- Only visible on running/queued jobs
- Sends `DELETE /jobs/{id}` or calls the IA with "cancel job {id}"
- Confirms visually when cancelled

## Visibility

The component slides in from below the chat input when the IA sends:

```json
{ "type": "custom", "component": "soofi-training-progress" }
```

It can be hidden via `[hide]` but persists in DOM so polling continues.
It re-shows automatically if a new job starts.

## Acceptance Criteria

- [ ] `<soofi-training-progress>` Lit component renders all training jobs
- [ ] Component polls `GET /jobs` every 3 s while jobs are active
- [ ] Phase names, progress percentages, and status are displayed
- [ ] Training metrics (loss, epoch, ETA) shown for active training phase
- [ ] Completed and failed jobs are shown (collapsed by default)
- [ ] Cancel button available on active jobs
- [ ] Component appears when IA sends `soofi-training-progress` custom component message
- [ ] Component is hideable but continues polling in background
- [ ] Training Gateway exposes `GET /jobs` and `GET /jobs/{id}` REST endpoints
- [ ] `VITE_TRAINING_GATEWAY_URL` passed as Vite build arg to soofi-ui

# Branches

- feature/T-08-5-training-progress-ui
