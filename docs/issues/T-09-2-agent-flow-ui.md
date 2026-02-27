# Task

- user story: [US-09](US-09-agent-observability.md)
- depends on: [T-07-6](T-07-6-interaction-agent.md)

/label ~UserStory_US-09
/label ~Task
/label ~ToDo

# Description

**Agent Flow Visualization (Frontend)**

Add a real-time architecture diagram to the A2UI frontend that animates when agents communicate.
The diagram reacts to existing AG-UI SSE events (`TOOL_CALL_START` / `TOOL_CALL_END`) — no new
backend infrastructure required.

## Tech Choice: SVG in a Lit Component

React-Flow is React-only and incompatible with our Lit Web Components stack. Use **inline SVG**
inside a `<soofi-agent-flow>` custom element:

- No new dependencies
- Full CSS animation control (keyframes for flowing dots)
- Responsive via `viewBox`
- Easy to extend with new nodes/edges as the architecture grows

## Diagram Layout

```
┌─────────┐      ┌──────────────────┐      ┌─────────┐
│   STT   │      │  Interaction     │      │  TTS    │
│ Service │─────▶│     Agent        │◀─────│ Service │
└─────────┘      └────────┬─────────┘      └─────────┘
                          │
                    A2A (ask_advisor_tool)
                          │
                   ┌──────▼──────┐
                   │   Advisor   │
                   │   Agent     │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐      ┌──────────┐
                   │ Vector MCP  │─────▶│ Weaviate │
                   └─────────────┘      └──────────┘

                   ┌─────────────────────────────────┐
                   │     H200  ░░░░░░░░░░  42% GPU   │  ← optional metric
                   └─────────────────────────────────┘
```

## Animation: Flowing Data Packets

When `TOOL_CALL_START { tool: "ask_advisor_tool" }` is received:

1. The edge between Interaction Agent and Advisor node glows (color: Soofi brand accent)
2. Small filled circles ("data packets") animate along the SVG path from source to target
   using `animateMotion` or CSS `offset-path`:

```css
@keyframes packet-flow {
  0%   { offset-distance: 0%; opacity: 1; }
  80%  { opacity: 1; }
  100% { offset-distance: 100%; opacity: 0; }
}
.packet {
  animation: packet-flow 0.8s ease-in-out infinite;
  offset-path: path("M 200,150 L 200,250");  /* SVG path of the edge */
}
```

When `TOOL_CALL_END` is received: animation stops, edge fades back to idle state.

## Event-to-Edge Mapping

| SSE Event | Tool | Animated Edge |
|-----------|------|---------------|
| `TOOL_CALL_START` | `ask_advisor_tool` | Interaction Agent → Advisor |
| `TOOL_CALL_START` | `show_dashboard` | Interaction Agent → (dashboard icon) |
| `TEXT_MESSAGE_START` | — | (Interaction Agent node pulses) |
| `RUN_FINISHED` | — | all edges idle |

## H200 GPU Load Indicator

A small bar/gauge in the diagram showing GPU utilization. Two options (choose at implementation
time):

**Option A — Triton Prometheus metrics** (real data, requires US-06 services running):
```
GET http://triton:8002/metrics → parse DCGM_FI_DEV_GPU_UTIL gauge → render %
Poll every 2s
```

**Option B — Simulated** (for demos without H200 connected):
```
Ramp from 5% to 70% during TOOL_CALL_START, decay back after TOOL_CALL_END
Pure CSS animation, no backend needed
```

Start with Option B; switch to Option A if H200 is available in the demo environment.

## Lit Component Interface

```ts
// Usage in main.ts:
html`<soofi-agent-flow .activeTools=${this.activeTools}></soofi-agent-flow>`
// activeTools: Set<string> — updated on TOOL_CALL_START/END
```

The component should be collapsible so it doesn't dominate the screen during normal chat use.

## Out of Scope

Source document preview and reranker relevance scores are handled in
[T-09-3](T-09-3-rag-transparency.md).

## Acceptance Criteria

- [ ] `<soofi-agent-flow>` Lit component renders the architecture diagram as SVG
- [ ] Diagram shows all active services: Interaction Agent, Advisor, Vector MCP, Weaviate, STT, TTS
- [ ] `TOOL_CALL_START / ask_advisor_tool` triggers animated data-packet flow on the correct edge
- [ ] `TOOL_CALL_END` stops animation; edge returns to idle
- [ ] GPU load indicator shown (simulated or real Triton metrics)
- [ ] Component is collapsible / non-intrusive during normal chat use
- [ ] Visually consistent with Soofi branding (colors, fonts)
- [ ] No new npm dependencies required

# Branches

- feature/T-09-2-agent-flow-ui
