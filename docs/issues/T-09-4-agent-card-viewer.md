# Task

- user story: [US-09](US-09-agent-observability.md)
- depends on: [T-07-6](T-07-6-interaction-agent.md), [T-02-5](T-02-5-docs-proxy.md)

/label ~UserStory_US-09
/label ~Task
/label ~ToDo

# Description

**Agent Card Viewer**

A new `show_agent_card` tool on the Interaction Agent that fetches an A2A agent card and renders
it as a formatted A2UI surface in the chat. Makes the A2A protocol tangible for demo audiences:
"These agents discover each other at runtime."

## Tool: `show_agent_card`

```python
@tool
async def show_agent_card(agent: str) -> str:
    """Show the A2A agent card for a registered agent.

    Args:
        agent: Agent name — "advisor", "training-agent", or "all".
    """
```

### Agent Registry

A simple dict mapping agent names to their A2A base URLs, configured via environment or
hardcoded for the known agents:

```python
AGENT_REGISTRY = {
    "interaction-agent": "http://localhost:8000/a2a/",
    "advisor": "http://advisor:8000/a2a/",
    "training-agent": "http://training-agent:8000/a2a/",
    "dataset-agent": "http://dataset-agent:8000/a2a/",
}
```

### Behavior

- `agent="advisor"` or `agent="training-agent"` — fetch that agent's card, return as A2UI surface
- `agent="all"` — fetch all cards, return as a list of surfaces
- Agent not found or unreachable — return a friendly error message

### Display

The agent card opens in the **side panel** (same panel used by the document viewer in T-02-5).
This gives a consistent "detail view" pattern — source documents and agent cards both open on
the right while the chat stays visible on the left.

The card is rendered as a formatted view showing:

- Agent name and description
- Protocol version
- Skills (name, description, tags)
- Capabilities (streaming, etc.)
- Status indicator (reachable / unreachable)

When `agent="all"`, the panel shows an accordion list (name + status). Click expands
the full card. With 4 agents (Interaction Agent, Advisor, Training Agent, Dataset Agent)
stacking would require too much scrolling.

### Prompt Addition

Add to the Interaction Agent system prompt:

```
- **show_agent_card**: Shows the A2A agent card for a registered agent.
  Use when the user asks about available agents, their capabilities, or agent cards.
```

## Example Interactions

- "Zeig mir die Agentenkarte vom Advisor"
- "Welche Agenten gibt es?"
- "Was kann der Training Agent?"

## Acceptance Criteria

- [ ] `show_agent_card` tool registered on the Interaction Agent
- [ ] Tool fetches `/.well-known/agent-card.json` from the target agent
- [ ] Agent card rendered as formatted A2UI surface (not raw JSON)
- [ ] `agent="all"` lists all available agents with their cards
- [ ] Unreachable agents shown with error state instead of crashing
- [ ] System prompt updated with tool description
- [ ] Works in the agent-flow SVG (tool call triggers TOOL_CALL_START/END)

# Branches

- feature/T-09-4-agent-card-viewer
