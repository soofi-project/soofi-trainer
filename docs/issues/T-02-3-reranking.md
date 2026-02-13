# Task

- user story: [US-02](US-02-knowledge-base.md)

/label ~UserStory_US-02
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Reranking for Search Results**

Add a reranking step to the Vector MCP `search_documents` tool. After Weaviate returns initial results via semantic search, a reranker model re-scores them for relevance before returning them to the caller.

## Motivation

Pure vector similarity can miss nuances — a reranker (cross-encoder) considers query and document jointly and produces more accurate relevance scores, especially for domain-specific content like LLM specialization methods.

## Architecture

```
Query → Weaviate (Top-N candidates) → Reranker Container (re-score) → Top-K results → Caller
```

The reranker runs as a dedicated Docker container in the stack (cross-encoder, self-hosted). Vector MCP calls the reranker via HTTP. Reranking is transparent to consumers — `search_documents` fetches more candidates than requested (Top-N, e.g. 20), sends them to the reranker, and returns the final Top-K (e.g. 5).

## Reranker Container

- **Model**: `BAAI/bge-reranker-v2-m3` (multilingual, ~568M parameters, ~1.1 GB RAM in float16)
- Runs on **CPU**, no GPU required
- Simple HTTP service (e.g. FastAPI + sentence-transformers or via [LocalAI](https://localai.io/features/reranker/))
- Added as a service in `docker-compose.yml`
- Only reachable within the Docker network (no external port needed)

## Implementation

- Add reranker container as a new service in `docker-compose.yml`
- Vector MCP calls the reranker via HTTP (internal Docker network)
- Reranking is optional and toggleable via `RERANKER_ENABLED=true/false`
- Reranker model configurable via `RERANKER_MODEL` (default: `BAAI/bge-reranker-v2-m3`)
- Candidate pool size (Top-N before reranking) configurable

## Acceptance Criteria

- [ ] Reranker runs as a dedicated container in the Docker Compose stack
- [ ] `search_documents` returns reranked results when enabled
- [ ] Reranker model is configurable via environment variable
- [ ] Reranking can be disabled without code changes (`RERANKER_ENABLED`)
- [ ] Candidate pool size (Top-N) is configurable
- [ ] Search quality improves measurably compared to pure vector search
- [ ] No breaking changes to the `search_documents` API

# Branches


