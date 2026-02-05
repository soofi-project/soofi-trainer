# Task

- user story: #US-04

/label ~UserStory_US-04
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**End-to-End Test**

Test the complete flow and document the results.

## Test Scenario

**User**: Developer wants to build a customer service chatbot

**Conversation**:
```
User: "Ich möchte einen Chatbot für unseren Kundenservice erstellen.
       Wir haben ein FAQ-Dokument mit etwa 200 Fragen und Antworten."

Agent: [Asks clarifying questions about update frequency, response time needs, etc.]

User: "Die FAQs ändern sich etwa einmal pro Monat.
       Antwortzeit ist nicht kritisch."

Agent: [Retrieves knowledge about RAG vs Fine-Tuning]
       [Recommends RAG with reasoning]
       [Explains next steps]
```

## Checkpoints

- [ ] Services start: `./up.sh`
- [ ] Weaviate healthy: `curl http://localhost:8070/v1/.well-known/ready`
- [ ] Vector MCP healthy: `curl http://localhost:8113/health`
- [ ] Knowledge searchable: test query via MCP Inspector
- [ ] Agent conversation flows naturally
- [ ] Recommendations cite knowledge base content
- [ ] Services stop: `./down.sh`

## Logging Commands

```bash
# Weaviate logs
docker logs soofi-weaviate

# Vector MCP logs (shows search queries)
docker logs soofi-vector-mcp

# Agent logs (if separate container)
docker logs soofi-agent
```

## Documentation Checklist

- [ ] README.md explains setup
- [ ] Architecture diagram is accurate
- [ ] All URLs documented
- [ ] Troubleshooting section exists

# Branches

- feature/US-04-integration
