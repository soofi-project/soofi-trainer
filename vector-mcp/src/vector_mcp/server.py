"""
MCP Server for Soofi Knowledge Base Search
"""

import logging
import os
from typing import Any

import httpx
import uvicorn
import weaviate
from weaviate.classes.query import Filter, MetadataQuery
from fastmcp import FastMCP
from langchain.embeddings.base import init_embeddings
from langchain_openai import OpenAIEmbeddings

# -------------------------------------------------
# Logging
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# FastMCP setup
# -------------------------------------------------
mcp = FastMCP("soofi-vector-mcp")

# -------------------------------------------------
# Embedding model (singleton)
# -------------------------------------------------
_embeddings = None


def get_embeddings():
    """
    Initialize embedding model from EMBEDDING_MODEL env var.
    Format: 'provider:model-name' e.g. 'openai:text-embedding-3-large'
    API keys are read automatically from standard env vars (OPENAI_API_KEY, etc.)
    """
    global _embeddings

    if _embeddings is None:
        model = os.getenv("EMBEDDING_MODEL")
        if not model:
            raise RuntimeError(
                "EMBEDDING_MODEL env var required. "
                "Format: 'provider:model-name' e.g. 'openai:text-embedding-3-large'"
            )
        logger.info(f"Initializing embedding model: {model}")
        _embeddings = init_embeddings(model)
        if isinstance(_embeddings, OpenAIEmbeddings):
            _embeddings.check_embedding_ctx_length = False

    return _embeddings


# -------------------------------------------------
# Reranker (optional, Qwen3-Reranker via vLLM on H200)
# -------------------------------------------------
RERANKER_ENABLED = os.getenv("RERANKER_ENABLED", "false").lower() == "true"

if RERANKER_ENABLED:
    RERANKER_URL = os.getenv("RERANKER_URL")
    if not RERANKER_URL:
        raise RuntimeError("RERANKER_URL env var required when RERANKER_ENABLED=true")
    _candidate_limit = os.getenv("RERANKER_CANDIDATE_LIMIT")
    if not _candidate_limit:
        raise RuntimeError("RERANKER_CANDIDATE_LIMIT env var required when RERANKER_ENABLED=true")
    RERANKER_CANDIDATE_LIMIT = int(_candidate_limit)
    logger.info(f"Reranker enabled: url={RERANKER_URL} candidate_limit={RERANKER_CANDIDATE_LIMIT}")
else:
    RERANKER_URL = ""
    RERANKER_CANDIDATE_LIMIT = 0
    logger.info("Reranker disabled")

_reranker_client: httpx.Client | None = None


def get_reranker_client() -> httpx.Client:
    global _reranker_client
    if _reranker_client is None:
        _reranker_client = httpx.Client(base_url=RERANKER_URL, timeout=10.0)
    return _reranker_client


def rerank(query: str, texts: list[str]) -> list[dict[str, Any]] | None:
    """Call vLLM reranker. Returns sorted [{"index": int, "score": float}] or None on failure."""
    if not texts:
        return []
    logger.info(f"Reranking {len(texts)} candidates for query='{query[:80]}'")
    try:
        import time
        t0 = time.perf_counter()
        resp = get_reranker_client().post(
            "/rerank",
            json={
                "model": os.getenv("RERANKER_MODEL", "qwen3-reranker-4b"),
                "query": query,
                "documents": texts,
            },
        )
        resp.raise_for_status()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        results = resp.json()["results"]
        ranked = [
            {"index": r["index"], "score": r["relevance_score"]}
            for r in results  # vLLM returns pre-sorted by relevance descending
        ]
        logger.info(
            f"Reranking done in {elapsed_ms:.0f}ms: top score={ranked[0]['score']:.4f}, "
            f"bottom score={ranked[-1]['score']:.4f}"
        )
        return ranked
    except Exception:
        logger.warning("Reranker unavailable, falling back to vector-only ranking", exc_info=True)
        return None


# -------------------------------------------------
# Weaviate client (singleton)
# -------------------------------------------------
_client: weaviate.WeaviateClient | None = None


def get_client() -> weaviate.WeaviateClient:
    """
    Create or return a singleton Weaviate v4 client.
    """
    global _client

    if _client is None:
        scheme = os.getenv("WEAVIATE_SCHEME")
        host = os.getenv("WEAVIATE_HOST")
        port_str = os.getenv("WEAVIATE_PORT")

        logger.info(f"Connecting to Weaviate at {scheme}://{host}:{port_str}")

        if not scheme:
            raise RuntimeError("WEAVIATE_SCHEME env var required.")
        if scheme != "http":
            raise RuntimeError("Only http scheme supported in this setup")
        if not host:
            raise RuntimeError("WEAVIATE_HOST env var required.")
        if not port_str:
            raise RuntimeError("WEAVIATE_PORT env var required.")

        port = int(port_str)

        _client = weaviate.connect_to_local(
            host=host,
            port=port,
        )

    return _client


# -------------------------------------------------
# Tools
# -------------------------------------------------
@mcp.tool()
def search_documents(
    query: str,
    filters: dict[str, str] | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """
    Semantic search over the Soofi knowledge base.

    Use list_metadata to discover available filter fields and values.

    Args:
        query: Natural language search query.
        filters: Optional metadata filters as key-value pairs (e.g. {"topic": "rag"}).
        limit: Maximum number of results.

    Returns:
        Search results with text, metadata and similarity distance.
    """
    try:
        client = get_client()

        collection_name = os.getenv("WEAVIATE_COLLECTION")

        if not collection_name:
            raise RuntimeError("WEAVIATE_COLLECTION env var required.")
    
        collection = client.collections.get(collection_name)

        filters_applied = filters or {}
        # Coerce list values to string — some models pass ["rag"] instead of "rag"
        filters_applied = {
            k: v[0] if isinstance(v, list) and v else str(v) if not isinstance(v, str) else v
            for k, v in filters_applied.items()
        }
        where_filter = None

        for field, value in filters_applied.items():
            f = Filter.by_property(field).equal(value)
            where_filter = (where_filter & f) if where_filter else f

        logger.info(
            f"Searching query='{query}' filters={filters_applied}"
        )

        embeddings = get_embeddings()
        query_vector = embeddings.embed_query(query)

        # Fetch more candidates when reranker is enabled
        fetch_limit = RERANKER_CANDIDATE_LIMIT if RERANKER_ENABLED else limit

        search_kwargs = {
            "near_vector": query_vector,
            "limit": fetch_limit,
            "return_metadata": MetadataQuery(distance=True),
        }
        if where_filter:
            search_kwargs["filters"] = where_filter

        response = collection.query.near_vector(**search_kwargs)

        results = []
        for obj in response.objects:
            props = dict(obj.properties)
            text = props.pop("text", None)
            results.append(
                {
                    "text": text,
                    "metadata": props,
                    "distance": float(obj.metadata.distance)
                    if obj.metadata and obj.metadata.distance is not None
                    else None,
                }
            )

        # Rerank if enabled
        reranker_used = False
        if RERANKER_ENABLED and results:
            texts = [r["text"] or "" for r in results]
            ranked = rerank(query, texts)
            if ranked is not None:
                reranked = []
                for i, item in enumerate(ranked[:limit]):
                    result = results[item["index"]]
                    result["reranker_score"] = round(float(item["score"]), 4)
                    reranked.append(result)
                    text_preview = (result["text"] or "")[:80].replace("\n", " ")
                    logger.info(
                        f"  #{i+1} score={item['score']:.4f} "
                        f"dist={result['distance']:.4f} "
                        f"| {text_preview}..."
                    )
                results = reranked
                reranker_used = True
            else:
                results = results[:limit]
        else:
            results = results[:limit]

        return {
            "results": results,
            "total": len(results),
            "query": query,
            "filters_applied": filters_applied,
            "reranker_used": reranker_used,
        }

    except Exception as e:
        logger.error("Search error", exc_info=True)
        return {
            "error": str(e),
            "results": [],
            "total": 0,
            "query": query,
            "filters_applied": {},
        }


@mcp.tool()
def list_metadata() -> dict[str, Any]:
    """
    List all metadata fields and their unique values from the knowledge base.

    Use this to discover available filter options for search_documents.

    Returns:
        A map of field names to their unique values,
        e.g. {"topic": ["rag", "fine_tuning"], "category": ["best_practice", "pitfall"]}.
    """
    try:
        client = get_client()
        collection_name = os.getenv("WEAVIATE_COLLECTION")

        if not collection_name:
            raise RuntimeError("WEAVIATE_COLLECTION env var required.")
        
        collection = client.collections.get(collection_name)

        schema = collection.config.get()
        fields = [
            p.name for p in schema.properties
            if p.name != "text"
        ]

        metadata = {}
        for field in fields:
            response = collection.aggregate.over_all(group_by=field)
            values = []
            for group in response.groups:
                if group.grouped_by and group.grouped_by.value:
                    values.append(str(group.grouped_by.value))
            metadata[field] = sorted(values)

        return {"metadata": metadata}

    except Exception as e:
        logger.error("Metadata listing error", exc_info=True)
        return {"error": str(e), "metadata": {}}


# -------------------------------------------------
# HTTP / ASGI entrypoint
# -------------------------------------------------
if __name__ == "__main__":
    app = mcp.http_app(path="/mcp")
    port_str = os.getenv("MCP_SERVER_PORT")

    if not port_str:
        raise RuntimeError("MCP_SERVER_PORT env var required.")

    port = int(port_str)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
