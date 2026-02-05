# Task

- user story: #US-02

/label ~UserStory_US-02
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Create Knowledge Collection**

Set up the Weaviate collection for agent knowledge.

## Collection Schema

```python
collection_name = "SoofiKnowledge"

properties = [
    {"name": "text", "dataType": ["text"]},
    {"name": "topic", "dataType": ["text"]},      # "rag", "fine_tuning", "comparison"
    {"name": "source", "dataType": ["text"]},     # URL or document name
    {"name": "category", "dataType": ["text"]},   # "best_practice", "pitfall", "use_case"
]
```

## Embedding Model

Use the same embedding model as configured in Vector MCP:
- Default: `openai:text-embedding-3-small`
- Alternative: `ollama:nomic-embed-text` (local)

## Setup Script

Create a Python script `scripts/init_collection.py` that:
1. Connects to Weaviate
2. Creates the collection if not exists
3. Configures the schema

# Branches

- feature/US-02-knowledge-base
