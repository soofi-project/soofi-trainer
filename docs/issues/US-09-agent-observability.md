# User story

- tasks:
  - [T-09-1](T-09-1-langfuse.md)
  - [T-09-2](T-09-2-agent-flow-ui.md)
  - [T-09-3](T-09-3-rag-transparency.md)
  - [T-09-4](T-09-4-agent-card-viewer.md)
  - [T-09-5](T-09-5-gpu-monitoring.md)

/label ~UserStory_US-09
/label ~UserStory

# Story

*"As a demo presenter, I want to see how messages flow through the agent system in real time,
so that I can make the multi-agent architecture tangible and impressive for an audience."*

# Description

Soofi's multi-agent architecture (Interaction Agent → Advisor → Vector MCP → Weaviate) is
invisible to users — they only see the chat. This user story makes the architecture observable
at two levels:

1. **Frontend visualization** ([T-09-2](T-09-2-agent-flow-ui.md)): An animated architecture
   diagram in the A2UI frontend that reacts to real agent events (TOOL_CALL_START/END).
   No new backend infrastructure needed — the AG-UI SSE stream already carries these events.

2. **Deep tracing** ([T-09-1](T-09-1-langfuse.md)): Langfuse running locally in Docker,
   integrated via the LangGraph callback handler. Shows full trace trees, token counts, and
   per-node latency — useful for development and for showing "real" observability to technical
   audiences.

## Why not Hubble (Cilium)?

Hubble is designed for Kubernetes + Cilium CNI. In a Docker Compose setup it would require
rebuilding the host network stack — high risk, no reward for our use case. Hubble also knows
nothing about agent logic (it sees TCP packets, not "Advisor started RAG search"). Skip it.

## Architecture Fit

The AG-UI SSE protocol is already the single channel between frontend and backend.
`TOOL_CALL_START` / `TOOL_CALL_END` events map directly to inter-agent communication because
every A2A call from the Interaction Agent is a LangGraph tool call. No new event types or
backend changes are needed for the frontend visualization.

```
SSE stream → Frontend
  TOOL_CALL_START { tool: "ask_advisor_tool" }
    → Interaction Agent → Advisor edge lights up, data packets flow
  TOOL_CALL_END { tool: "ask_advisor_tool" }
    → edge fades
```

When T-07-7 (Async A2A Status Push) is implemented, status labels (e.g.
"Suche in Wissensdatenbank…") will be available as additional annotations on the edges.

## Acceptance Criteria

- [ ] Langfuse runs as a local Docker service and receives traces from all LangGraph agents
- [ ] LangGraph callback handler configured for Interaction Agent and Advisor
- [ ] Frontend shows an architecture diagram of all Soofi services/agents
- [ ] Diagram animates in real time based on TOOL_CALL_START/END events
- [ ] Data-packet animation visible when Interaction Agent calls Advisor
- [ ] H200 GPU load indicator shown in diagram (Triton metrics or simulated)
- [ ] RAG transparency panel shows retrieved source documents and reranker relevance scores
- [ ] Relevance scores tied visually to advisor "decline" behavior (low score → no answer)
- [ ] Visualization is visually compelling for a demo audience
