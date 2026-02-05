# Task

- user story: #US-03

/label ~UserStory_US-03
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Implement LangGraph Agent**

Create the agent using LangGraph with Vector MCP integration.

## Agent Structure

```python
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI

# State definition
class AgentState(TypedDict):
    messages: list
    context: str  # Retrieved knowledge
    recommendation: str | None

# Graph
graph = StateGraph(AgentState)
graph.add_node("retrieve", retrieve_knowledge)  # Call Vector MCP
graph.add_node("respond", generate_response)    # LLM response
```

## Vector MCP Integration

The agent calls the Vector MCP server to retrieve knowledge:

```python
async def retrieve_knowledge(state: AgentState) -> AgentState:
    # Call Vector MCP search_documents
    response = await httpx.post(
        "http://vector-mcp:8000/tools/search_documents",
        json={
            "query": extract_query(state["messages"]),
            "submodel_id": "soofi-knowledge",  # or similar identifier
            "limit": 5
        }
    )
    state["context"] = format_results(response.json())
    return state
```

## Files to Create

```
agent/
├── __init__.py
├── graph.py          # LangGraph definition
├── prompts.py        # System and state prompts
├── tools.py          # Vector MCP client
└── server.py         # FastAPI wrapper (optional)
```

# Branches

- feature/US-03-agent-architecture
