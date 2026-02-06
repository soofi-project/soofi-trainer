# Task

- user story: #US-02

/label ~UserStory_US-02
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Knowledge Documents for LLM Specialization Methods**

Create markdown documents covering all LLM specialization methods and related best practices. These files are placed in the `knowledge/` folder and automatically ingested into Weaviate by the ingestion container (T-02-1).

## Folder Structure

```
knowledge/
├── methods/              → one file per specialization method
├── rag/                  → RAG best practices, pitfalls, use cases
├── fine_tuning/          → Fine-tuning best practices, pitfalls, use cases
└── comparison/           → When to use which method
```

## Methods to Document

| # | Method | Key Focus |
|---|--------|-----------|
| 1 | Continued Pretraining | Large unlabeled domain data |
| 2 | Supervised Fine-Tuning (SFT) | Labeled input-output pairs |
| 3 | LoRA | Limited GPU resources, fast iteration |
| 4 | QLoRA | Consumer GPUs, large models |
| 5 | Prefix Tuning / P-Tuning | Very small datasets, minimal modification |
| 6 | Instruction Tuning | Chatbot/assistant applications |
| 7 | RLHF | Human alignment, safety |
| 8 | DPO | Preference data, simpler than RLHF |
| 9 | RAG | Dynamic knowledge, no training |
| 10 | Knowledge Distillation | Deployment constraints, smaller models |

## Document Format per Method

Each method document should cover:
- **Overview**: Brief description of the method and how it works
- **When to Use**: Scenarios where this method is appropriate
- **Pros and Cons**: Advantages and disadvantages
- **Resource Requirements**: Hardware, data, time, cost
- **Example Use Cases**: Concrete examples

## Additional Documents

- **RAG best practices and pitfalls** (e.g. chunking strategies, embedding model mismatch)
- **Fine-tuning best practices and pitfalls** (e.g. overfitting on small datasets)
- **Comparison**: When to use which method, decision guidance

## Content Sources

Curate content from:
- OpenAI Fine-Tuning Guide
- LangChain RAG Documentation
- HuggingFace Training Tutorials
- Blog posts comparing RAG vs Fine-Tuning
- Academic papers and surveys

## Acceptance Criteria

- [ ] All 10 methods documented as individual markdown files
- [ ] Pros/cons for each method documented
- [ ] Resource requirements described per method
- [ ] Use cases clearly described
- [ ] RAG best practices and pitfalls documented
- [ ] Fine-tuning best practices and pitfalls documented
- [ ] Comparison document covers when to use which method
- [ ] All documents are ingested successfully by the ingestion container

# Branches

- feature/US-02-knowledge-base
