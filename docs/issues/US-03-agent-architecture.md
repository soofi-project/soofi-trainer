# User Story

- tasks:
  - #T-03-1
  - #T-03-2
  - #T-03-3

/label ~UserStory
/milestone %ProductBacklog

# Story

*"As a user, I want to interact with an intelligent agent that guides me through choosing the right approach (RAG vs. Fine-Tuning) and provides expert recommendations."*

# Description

The agent is the heart of Soofi Trainer. It guides users through a structured conversation:

1. **Understand the goal**: What does the user want to achieve?
2. **Gather context**: What data is available? What are the constraints?
3. **Retrieve knowledge**: Search the knowledge base for relevant information
4. **Recommend approach**: RAG or Fine-Tuning with reasoning
5. **Explain next steps**: How to proceed with the chosen approach

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Open WebUI │────▶│   Agent     │────▶│ Vector MCP  │
└─────────────┘     │ (LangGraph) │     │  (RAG)      │
                    └─────────────┘     └─────────────┘
```

The agent uses:
- **LangGraph** for conversation state management
- **Vector MCP** for knowledge retrieval (RAG)
- **OpenAI API** for language model

## Agent Behavior

- Communicates in German (friendly, professional)
- Asks clarifying questions when needed
- Explains technical concepts in understandable terms
- Provides reasoned recommendations with pros/cons

# Acceptance Criterion

- [ ] Agent conducts structured conversation
- [ ] Agent retrieves relevant knowledge via Vector MCP
- [ ] RAG vs. Fine-Tuning recommendation works with reasoning
- [ ] Conversation state is maintained
- [ ] German prompts are understandable and professional
- [ ] Starter prompts available for Open WebUI
