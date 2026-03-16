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

- **Image**: [Hugging Face TEI](https://github.com/huggingface/text-embeddings-inference) (`ghcr.io/huggingface/text-embeddings-inference`)
- **Model**: `BAAI/bge-reranker-v2-m3` (multilingual, ~568M parameters)
- Runs on **GPU** (H200) — CPU inference is too slow (~1-3s for 20 docs, GPU <50ms)
- Only reachable within the Docker network (no external port needed)
- Model weights cached in external Docker volume (`reranker_model_cache`) to survive `down --clean`

## Implementation

- Add TEI reranker container as a new service in `docker-compose.yml`
- Use GPU-enabled TEI image with `deploy.resources.reservations.devices` for GPU access
- Vector MCP calls the reranker via HTTP (internal Docker network, `/rerank` endpoint)
- Reranking is optional and toggleable via `RERANKER_ENABLED=true/false`
- Reranker model configurable via `RERANKER_MODEL` (default: `BAAI/bge-reranker-v2-m3`)
- Candidate pool size (Top-N before reranking) configurable via `RERANKER_CANDIDATE_LIMIT`
- Graceful degradation: if reranker is unavailable, search falls back to unranked results

## Findings

- **Custom service vs. pre-built image**: Evaluated building a custom FastAPI + torch service vs. using pre-built images (Infinity, TEI). TEI is the best option: ~500 MB (CPU) image, Rust-based, officially maintained by Hugging Face.
- **Infinity** (`michaelf34/infinity`): Supports `trust_remote_code` and more models, but image is ~4-5 GB. Overkill for a single reranker.
- **Jina Reranker v3** (`jinaai/jina-reranker-v3`): Requires `trust_remote_code=True`, which TEI does not support. Ruled out in favor of `bge-reranker-v2-m3`.
- **CPU vs. GPU**: CPU reranking of 20 documents takes ~1-3s (unacceptable for chat latency). GPU (H200) brings this down to <50ms. GPU is required.
- **TEI API format**: `POST /rerank` with `{"query": "...", "texts": [...]}`, response `{"results": [{"index": 0, "relevance_score": 0.95}, ...]}`.

## Acceptance Criteria

- [ ] Reranker runs as a dedicated container in the Docker Compose stack (TEI with GPU)
- [ ] `search_documents` returns reranked results when enabled
- [ ] Reranker model is configurable via environment variable
- [ ] Reranking can be disabled without code changes (`RERANKER_ENABLED`)
- [ ] Candidate pool size (Top-N) is configurable
- [ ] Search quality improves measurably compared to pure vector search
- [ ] No breaking changes to the `search_documents` API

# Branches

- `feature/T-02-3-reranking`
