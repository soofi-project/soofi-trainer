# User Story

- tasks:
  - #T-02-1
  - #T-02-2
  - #T-02-3

/label ~UserStory
/milestone %ProductBacklog

# Story

*"As a user, I want the agent to have expert knowledge about RAG, Fine-Tuning, and all LLM specialization methods, so that it can give me well-founded recommendations."*

# Description

The agent needs a knowledge base to provide expert advice. This knowledge is stored in Weaviate and accessed via the Vector MCP server.

## Knowledge Topics

The agent should know about:
- When to use RAG vs. Fine-Tuning
- Pros and cons of each approach
- Best practices for both methods
- Common pitfalls and how to avoid them
- Cost and resource considerations
- Example use cases
- **All LLM Specialization Methods** (see T-02-3):
  - Continued Pretraining
  - Supervised Fine-Tuning (SFT)
  - LoRA (Low-Rank Adaptation)
  - QLoRA (Quantized LoRA)
  - Prefix Tuning / P-Tuning
  - Instruction Tuning
  - RLHF (Reinforcement Learning from Human Feedback)
  - DPO (Direct Preference Optimization)
  - Knowledge Distillation

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│     Agent       │────▶│   Vector MCP    │────▶│   Weaviate   │
│  (LangGraph)    │     │ (search_documents)│   │ (Knowledge)  │
└─────────────────┘     └─────────────────┘     └──────────────┘
```

The Vector MCP server (`dfkibasys/aas-vector-mcp`) provides:
- `search_documents` - Semantic search over knowledge base
- `list_metadata_values` - List available topics/categories

# Acceptance Criterion

- [ ] Weaviate collection "SoofiKnowledge" exists
- [ ] At least 10 documents about RAG/Fine-Tuning ingested
- [ ] Knowledge about all 10 specialization methods ingested (T-02-3)
- [ ] Agent can retrieve relevant knowledge via Vector MCP
- [ ] Search results are relevant to user queries
