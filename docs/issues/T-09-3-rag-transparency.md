# Task

- user story: [US-09](US-09-agent-observability.md)
- depends on:
  - [T-02-3](T-02-3-reranking.md)
  - [T-07-7](T-07-7-a2a-status-push.md)

/label ~UserStory_US-09
/label ~Task
/label ~ToDo

# Description

**RAG Transparency Panel ("Thinking Bubble")**

Show the user which source documents were retrieved from Weaviate and how relevant they are,
while the Advisor is still processing. Makes the RAG pipeline tangible for demo audiences:
"The system doesn't guess — it reads your documents."

## What the Panel Shows

```
┌─────────────────────────────────────────────────────┐
│ 🔍 Suche in Wissensdatenbank…                       │
│                                                     │
│ 📄 2024-llm-finetuning-guide.pdf                    │
│    Abschnitt: LoRA Hyperparameter          ████ 94% │
│                                                     │
│ 📄 dfki-rag-best-practices.md                       │
│    Abschnitt: Chunk-Strategie              ███░ 81% │
└─────────────────────────────────────────────────────┘
```

- Source file name + section title (from vector-mcp metadata)
- Reranker relevance score as a bar (not labeled "confidence" — labeled "Quellen-Relevanz")
- Panel appears on `TOOL_CALL_START / ask_advisor_tool`, fades out on `TOOL_CALL_END`

## Why Reranker Score (not Raw Vector Distance)

Raw cosine similarity is a query-embedding distance — it's not semantically interpretable as
relevance. The reranker (T-02-3) is a cross-encoder trained to score query-document relevance
directly. Its score is:

- More meaningful: trained on actual relevance judgements
- Tied to advisor behavior: the advisor already declines to answer when no high-scoring
  chunks are found (see advisor prompts). So a low score visibly explains *why* the advisor
  says "Ich kann dazu nichts finden."
- Honest label: "Quellen-Relevanz" or "Abdeckung in der Wissensdatenbank" — not "Konfidenz"

## Changes Required

### 1. vector-mcp (`vector-mcp/src/`)
Include reranker scores and section metadata in the `search_documents` tool output.
Currently only text content is returned; add:
```json
{
  "text": "...",
  "source_file": "2024-llm-finetuning-guide.pdf",
  "section_title": "LoRA Hyperparameter",
  "reranker_score": 0.94
}
```

### 2. Advisor (`advisor/src/`)
After `search_documents` completes, emit an A2A intermediate status event (via the mechanism
implemented in T-07-7) containing the top-N source names and reranker scores:
```json
{
  "type": "rag_sources",
  "sources": [
    {"file": "2024-llm-finetuning-guide.pdf", "section": "LoRA Hyperparameter", "score": 0.94},
    {"file": "dfki-rag-best-practices.md", "section": "Chunk-Strategie", "score": 0.81}
  ]
}
```

### 3. Interaction Agent (`interaction-agent/src/agent.py`)
Parse the `rag_sources` status event from the A2A stream and forward it as a new SSE event
to the browser:
```json
{"type": "RAG_SOURCES", "sources": [...]}
```

### 4. Frontend (`soofi-ui/src/main.ts`)
Handle `RAG_SOURCES` event: render the transparency panel. The panel can be part of
`<soofi-agent-flow>` (T-09-2) or a standalone `<soofi-rag-panel>` component — decide at
implementation time based on layout.

## Acceptance Criteria

- [ ] `search_documents` tool output includes `source_file`, `section_title`, `reranker_score`
- [ ] Advisor emits `rag_sources` A2A status event after retrieval (before LLM generation)
- [ ] Interaction Agent forwards it as `RAG_SOURCES` SSE event to browser
- [ ] Frontend panel shows source file names, section titles, and relevance bars
- [ ] Panel appears during Advisor tool call, fades after `TOOL_CALL_END`
- [ ] Relevance bar labeled "Quellen-Relevanz" (not "Konfidenz")
- [ ] Low relevance scores (e.g. all < 0.5) visually indicate weak knowledge base coverage
- [ ] No panel shown when Advisor does not use `search_documents` (e.g. greeting)

# Branches

- feature/T-09-3-rag-transparency
