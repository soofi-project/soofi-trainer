# User Story

- tasks:
  - #T-05-1

/label ~UserStory
/milestone %ProductBacklog

# Story

*"As a developer, I want to test the complete flow end-to-end, so that I can be sure all components work together."*

# Description

The integration ensures that all components work together seamlessly:

- Open WebUI → Agent → Vector MCP → Weaviate
- Open WebUI → Agent → HuggingFace MCP → HuggingFace Hub
- Open WebUI → Agent → Eclipse Dataspace MCP → Eclipse Dataspace
- Knowledge retrieval returns relevant results
- Agent provides coherent recommendations
- Error handling works properly

## Test Flow

1. User opens Open WebUI
2. User describes their use case
3. Agent asks clarifying questions
4. Agent retrieves relevant knowledge
5. Agent searches for datasets (HuggingFace, Eclipse Dataspace) if needed
6. Agent provides recommendation with reasoning
7. User can ask follow-up questions

# Acceptance Criteria

- [ ] All services start without errors (`./up.sh`)
- [ ] Open WebUI shows chat interface
- [ ] Agent responds in German
- [ ] Knowledge retrieval works (check Vector MCP logs)
- [ ] HuggingFace dataset search works
- [ ] Eclipse Dataspace dataset search works
- [ ] Recommendation includes reasoning from knowledge base
- [ ] `./down.sh` stops everything cleanly
- [ ] Documentation is complete
