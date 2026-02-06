# Task

- user story: #US-03

/label ~UserStory_US-03
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Implement LangGraph Agent**

Create the agent using LangGraph with Vector MCP integration. The agent replaces the temporary n8n chatbot (T-01-3) and provides the full conversation and recommendation flow. Open WebUI connects to the LangGraph agent as its backend.

## Agent Responsibilities

- Manage conversation state across multiple turns
- Retrieve relevant knowledge from Weaviate via the Vector MCP server
- Generate responses using an LLM (OpenAI API)
- Maintain context about the user's situation throughout the conversation

## Key Components

| Component | Description |
|-----------|-------------|
| State management | Track messages, retrieved context, and recommendation status |
| Knowledge retrieval | Call the Vector MCP `search_documents` endpoint to find relevant knowledge |
| Response generation | Use the LLM with retrieved context to generate informed responses |

## Integration

- Open WebUI connects to the LangGraph agent as its backend (replaces n8n)
- The agent connects to the Vector MCP server to search the knowledge base
- The agent runs as a Docker container within the stack

## Acceptance Criteria

- [ ] LangGraph agent is implemented and runnable
- [ ] Agent retrieves knowledge from Vector MCP on relevant queries
- [ ] Agent maintains conversation state across turns
- [ ] Open WebUI connects to the agent as backend
- [ ] Agent runs as a container in the Docker stack

# Branches

- feature/US-03-agent-architecture
