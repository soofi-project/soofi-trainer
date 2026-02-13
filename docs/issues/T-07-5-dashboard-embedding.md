# Task

- user story: #US-07
- depends on: #T-07-1
- type: exploration

/label ~UserStory_US-07
/label ~Task
/label ~ToDo
/label ~Exploration

# Description

**Exploration: Dashboard Embedding**

Research and PoC for embedding external dashboards in the A2UI frontend via the `dashboard-embed` custom component (T-07-2). This is an exploration ticket — the goal is research and a working proof of concept, not a full production implementation.

## Candidates to Evaluate

### Grafana Dashboards (simplest option)
- Embed Grafana panels showing OpenTelemetry data
- Grafana supports iframe embedding with anonymous access or auth tokens
- Could show: request latency, token usage, error rates, pipeline traces
- Evaluate: embedding ease, authentication, responsive sizing

### Langfuse Traces/Sessions
- Embed Langfuse UI views showing agent traces and session history
- Useful for transparency: show the user what the agent is doing internally
- Evaluate: iframe support, authentication, relevant views to embed

### agntcy obs-api
- Container image: `ghcr.io/agntcy/obs-api:0.1.1`
- Agent communication scoring and observability
- Evaluate: what dashboards/views it provides, integration effort, value for Soofi

## Agent-Driven Display

The Interaction Agent (T-07-6) decides when and what dashboard to show based on conversation context:
- During execution phase → show training progress dashboard
- When discussing recommendations → show comparison metrics
- On request → show detailed traces or system health
- After A2A calls → show obs-api visualization of the agent-to-agent communication

The Interaction Agent sends an A2UI message referencing the `dashboard-embed` component with the appropriate URL and parameters.

## Out of Scope

- **Hubble** (Kubernetes/Cilium network visualization) — requires K8s migration first, not applicable to current Docker Compose setup

## Deliverables

- [ ] Research document comparing the three candidates (Grafana, Langfuse, obs-api)
- [ ] PoC: at least one dashboard embedded and rendering in the A2UI frontend
- [ ] Documentation of iframe embedding requirements (auth, CORS, sizing)
- [ ] Recommendation on which dashboards to integrate for the demo

## Acceptance Criteria

- [ ] At least one external dashboard renders inside the `dashboard-embed` component
- [ ] Interaction Agent can trigger dashboard display via A2UI messages
- [ ] Research document covers all three candidates with pros/cons
- [ ] Recommendation documented for which dashboards to use in production

# Branches

- feature/T-07-5-dashboard-embedding
