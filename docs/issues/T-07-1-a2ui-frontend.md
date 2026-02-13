# Task

- user story: #US-07

/label ~UserStory_US-07
/label ~Task
/label ~ToDo

# Description

**A2UI + Lit Frontend Scaffold**

Project scaffolding for the A2UI-based frontend as an **additional** service alongside Open WebUI. Uses the official Lit Web Components renderer (`@a2ui/web-lib`) to render agent-driven UI declaratively. Open WebUI remains in docker-compose as a lightweight testing interface for directly interacting with the backend agents.

## Scope

1. **npm project setup** with `@a2ui/web-lib` (Lit renderer) and build tooling
2. **Dockerfile** serving the built frontend (static files via nginx or similar), added as a new service in `docker-compose.yml`
3. **Basic A2UI message rendering**: text, cards, buttons
4. **Connection to agent backend** via SSE or WebSocket for streaming A2UI messages
5. **Minimal working page** that can receive and render A2UI messages from the agent

## Technical Details

### A2UI Integration

- Use the official `@a2ui/web-lib` package (Lit-based renderer, ~5kb)
- The Interaction Agent (T-07-6) sends JSON A2UI message descriptors
- The frontend renders them natively using Lit Web Components
- Use `ag-ui-langgraph` PyPI package on the agent side for LangGraph ↔ A2UI integration

### Docker Setup

- Add new `soofi-ui` service to `docker-compose.yml` (Open WebUI stays as-is)
- Multi-stage Dockerfile: build stage (Node) → serve stage (nginx)
- Expose on a dedicated external port (e.g. 3001) — Open WebUI keeps port 3000
- Connect to `soofi-network`

### Agent Connection

- SSE or WebSocket endpoint from the Interaction Agent (T-07-6)
- The frontend subscribes to a stream of A2UI message events from the Interaction Agent
- User input (text for now, voice later in T-07-3) is sent back to the Interaction Agent
- The frontend only communicates with the Interaction Agent — specialist agents are reached via A2A on the backend

## Key References

- A2UI spec: https://github.com/google/A2UI
- A2UI docs: https://a2ui.org/
- Lit: https://lit.dev/

## Acceptance Criteria

- [ ] npm project created with `@a2ui/web-lib` dependency
- [ ] Dockerfile builds and serves the frontend
- [ ] Frontend runs as `soofi-ui` service alongside Open WebUI in `docker-compose.yml`
- [ ] Basic A2UI message types render correctly (text, cards, buttons)
- [ ] Frontend connects to Interaction Agent (T-07-6) via SSE or WebSocket
- [ ] A2UI messages from the Interaction Agent appear in the browser in real-time
- [ ] `docker-compose up` starts both Open WebUI (:3000) and soofi-ui (:3001)

# Branches

- feature/T-07-1-a2ui-frontend
