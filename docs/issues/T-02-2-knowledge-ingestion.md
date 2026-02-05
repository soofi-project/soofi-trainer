# Task

- user story: #US-02

/label ~UserStory_US-02
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Ingest Knowledge Documents**

Populate the knowledge base with expert content about RAG and Fine-Tuning.

## Document Sources

Curate content from:
- OpenAI Fine-Tuning Guide
- LangChain RAG Documentation
- HuggingFace Training Tutorials
- Blog posts comparing RAG vs Fine-Tuning
- Best practice articles

## Content Categories

| Topic | Category | Example |
|-------|----------|---------|
| RAG | best_practice | "Use chunking with overlap for better context" |
| RAG | pitfall | "Embedding model mismatch between ingestion and query" |
| Fine-Tuning | best_practice | "Start with a small dataset and iterate" |
| Fine-Tuning | pitfall | "Overfitting on small datasets" |
| Comparison | use_case | "Use RAG when knowledge changes frequently" |

## Ingestion Script

Create `scripts/ingest_knowledge.py` that:
1. Reads documents from `knowledge/` folder
2. Chunks text appropriately
3. Embeds and stores in Weaviate

## Folder Structure

```
knowledge/
├── rag/
│   ├── best_practices.md
│   ├── pitfalls.md
│   └── use_cases.md
├── fine_tuning/
│   ├── best_practices.md
│   ├── pitfalls.md
│   └── use_cases.md
└── comparison/
    └── when_to_use_what.md
```

# Branches

- feature/US-02-knowledge-base
