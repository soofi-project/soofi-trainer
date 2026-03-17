# User story

- tasks:
  - [T-03-1](T-03-1-langgraph-agent.md) #9
  - [T-03-2](T-03-2-agent-prompts.md) #10
  - [T-03-3](T-03-3-decision-logic.md) #11
  - [T-03-4](T-03-4-ci-pipeline.md) #12

# Story

*"As a user, I want to interact with an intelligent agent that guides me through choosing the right LLM specialization approach and provides expert recommendations with structured reasoning."*

# Description

The agent is the heart of Soofi Trainer. It guides users through a structured conversation:

1. **Understand the goal**: What does the user want to achieve?
2. **Gather context**: What data is available? What are the constraints?
3. **Retrieve knowledge**: Search the knowledge base for relevant information
4. **Search datasets**: Find suitable datasets from external sources (HuggingFace, Eclipse Dataspace) if needed (via [US-04](US-04-dataset-search.md))
5. **Apply decision logic**: Use structured decision tree and multi-criteria evaluation ([T-03-3](T-03-3-decision-logic.md))
6. **Generate recommendation**: Create structured report with primary recommendation, alternatives, and next steps ([T-03-3](T-03-3-decision-logic.md))

## Architecture

The agent runs as a Docker container. Open WebUI connects to the agent as its backend (replacing the temporary n8n chatbot from [T-01-3](T-01-3-n8n-chatbot.md)).

The agent uses:
- **LangGraph** for conversation state management
- **Vector MCP** for knowledge retrieval (RAG)
- **OpenAI API** for language model

## Agent Behavior

- Communicates in German (friendly, professional)
- Asks clarifying questions when needed
- Explains technical concepts in understandable terms
- Provides reasoned recommendations with pros/cons

# Acceptance Criteria

- [ ] Agent conducts structured conversation
- [ ] Agent retrieves relevant knowledge via Vector MCP
- [ ] Agent uses decision logic to recommend appropriate method ([T-03-3](T-03-3-decision-logic.md))
- [ ] Agent generates structured recommendation reports ([T-03-3](T-03-3-decision-logic.md))
- [ ] Conversation state is maintained
- [ ] German prompts are understandable and professional
- [ ] Starter prompts available for Open WebUI
- [ ] CI pipeline runs unit tests on push/MR
