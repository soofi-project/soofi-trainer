# User Story

- tasks:
  - #T-04-1

/label ~UserStory
/milestone %ProductBacklog

# Story

*"As a developer, I want to test the complete flow end-to-end, so that I can be sure all components work together."*

# Description

The integration ensures that all components work together seamlessly:

- Open WebUI → Agent → Vector MCP → Weaviate
- Knowledge retrieval returns relevant results
- Agent provides coherent recommendations
- Error handling works properly

## Test Flow

1. User opens Open WebUI
2. User describes their use case
3. Agent asks clarifying questions
4. Agent retrieves relevant knowledge
5. Agent provides recommendation with reasoning
6. User can ask follow-up questions

# Acceptance Criterion

- [ ] All services start without errors (`./up.sh`)
- [ ] Open WebUI shows chat interface
- [ ] Agent responds in German
- [ ] Knowledge retrieval works (check Vector MCP logs)
- [ ] Recommendation includes reasoning from knowledge base
- [ ] `./down.sh` stops everything cleanly
- [ ] Documentation is complete
