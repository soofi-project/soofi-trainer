# User story

- tasks:
  - [T-07-1](T-07-1-a2ui-frontend.md)
  - [T-07-2](T-07-2-custom-components.md)
  - [T-07-3](T-07-3-voice-local.md)
  - [T-07-4](T-07-4-voice-h200.md)
  - [T-07-5](T-07-5-dashboard-embedding.md)
  - [T-07-6](T-07-6-interaction-agent.md)
  - [T-07-7](T-07-7-a2a-status-push.md)
  - [T-07-8](T-07-8-language-toggle.md)
  - [T-07-9](T-07-9-session-reset.md)

# Story

*"As a user, I want to interact with the Soofi agent via voice and a dynamic visual interface, so that the experience is more engaging and intuitive than a text chat."*

# Description

Open WebUI is a basic chat interface — functional but not impressive for demos (e.g. Hannover Messe). This user story replaces it with an agent-driven UI using Google's A2UI protocol, adding voice input/output and dynamic UI capabilities.

A2UI (v0.8, Apache 2.0) is a declarative JSON protocol where the agent sends UI descriptions and the client renders them natively. The Lit Web Components renderer is the official, lightweight (~5kb) option for browser-based apps.

A dedicated **Interaction Agent** ([T-07-6](T-07-6-interaction-agent.md)) owns the user-facing experience and communicates with specialist agents (analysis, recommendation, pipeline) via **A2A** (Agent-to-Agent protocol). This makes agent-to-agent communication — a core feature of Soofi — architecturally visible and demo-able, not just a claim.

The Interaction Agent controls what the user sees — pulsating logo during processing, embedded dashboards, voice controls — making the experience significantly more engaging than a text chat.

## Architecture

```
                         Browser (Lit/A2UI)
                              |
                         SSE / WebSocket
                              |
+----------------+    +---------------------+
|  STT Service   |<---|  Interaction Agent   |
|  (Whisper)     |    |    (LangGraph)      |
+----------------+    +---+------------+----+
                          |            |
+----------------+       A2A          A2A
|  TTS Service   |<--+   |            |
|  (Piper/F5)   |   | +--+--------+ +-+-----------+  +------------------+
+----------------+   | | Analysis  | |Recommendation|  |   Vector MCP     |
                     | | Agent     | |Agent         |  | (search_documents)|
                     | +-----------+ +-------------+  +--------+---------+
                     |                                          |
                     +------------------------------------------+
                                                        Weaviate
```

The A2UI frontend (`soofi-ui`) is added as a new service alongside Open WebUI in docker-compose. Open WebUI remains available for quick testing directly against the backend agents. The Interaction Agent ([T-07-6](T-07-6-interaction-agent.md)) is the only agent the A2UI frontend talks to — it delegates domain tasks to specialist agents via A2A. Voice services (STT/TTS) run as separate Docker containers, configurable for local (GPU) or cloud API usage.

## Sub-Tasks

| Task | Title | Dependencies |
|------|-------|--------------|
| [T-07-1](T-07-1-a2ui-frontend.md) | A2UI + Lit Frontend Scaffold | — |
| [T-07-2](T-07-2-custom-components.md) | Custom Components & Theming | [T-07-1](T-07-1-a2ui-frontend.md) |
| [T-07-3](T-07-3-voice-local.md) | Voice Pipeline (Local/Cloud) | [T-07-1](T-07-1-a2ui-frontend.md) |
| [T-07-4](T-07-4-voice-h200.md) | Voice on H200 (Production) | [T-07-3](T-07-3-voice-local.md) |
| [T-07-5](T-07-5-dashboard-embedding.md) | Dashboard Embedding (Exploration) | [T-07-1](T-07-1-a2ui-frontend.md) |
| [T-07-6](T-07-6-interaction-agent.md) | Interaction Agent (A2A Orchestrator) | [T-07-1](T-07-1-a2ui-frontend.md) |
| [T-07-7](T-07-7-a2a-status-push.md) | Async A2A Status Push | [T-07-6](T-07-6-interaction-agent.md) |
| [T-07-8](T-07-8-language-toggle.md) | Runtime Language Toggle (DE/EN) | [T-07-6](T-07-6-interaction-agent.md), [T-07-7](T-07-7-a2a-status-push.md) |
| [T-07-9](T-07-9-session-reset.md) | Session Reset Button | [T-07-6](T-07-6-interaction-agent.md) |

## Future Extensions

- **Reachy Mini**: If the robot arrives, a separate user story will cover Reachy Mini integration via MCP (see https://github.com/jackccrawford/reachy-mini-mcp). This is intentionally out of scope for US-07.

## Key References

- A2UI spec & Lit renderer: https://github.com/google/A2UI
- A2UI docs: https://a2ui.org/
- A2A (Agent-to-Agent) protocol: https://google.github.io/A2A/
- ag-ui-langgraph PyPI package for LangGraph integration
- A2UI Composer (visual builder): referenced in A2UI docs

# Acceptance Criteria

- [ ] A2UI + Lit frontend runs as `soofi-ui` service alongside Open WebUI in docker-compose
- [ ] Interaction Agent sends A2UI messages and the frontend renders them (text, cards, buttons)
- [ ] Interaction Agent communicates with specialist agents via A2A
- [ ] Custom Soofi components (logo, voice controls, dashboard embed) are registered and functional
- [ ] Voice input works: user speaks → STT → Interaction Agent → specialist agents → response
- [ ] Voice output works: agent response → TTS → audio playback
- [ ] Voice pipeline runs locally on H200 with GPU acceleration
- [ ] Soofi branding and theming applied to the frontend
- [ ] Agent-to-agent communication is observable and demo-able
- [ ] Dashboard embedding explored and documented (PoC)
