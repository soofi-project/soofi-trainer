"""
MCP Server for Soofi Knowledge Base Search
"""

import logging
import os
from typing import Any

import uvicorn
import weaviate
from weaviate.classes.query import Filter, MetadataQuery
from fastmcp import FastMCP
from langchain.embeddings.base import init_embeddings

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

    return _embeddings

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

        logger.info(f"Connecting to Weaviate at {scheme}://{host}:{port}")

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
        where_filter = None

        for field, value in filters_applied.items():
            f = Filter.by_property(field).equal(value)
            where_filter = (where_filter & f) if where_filter else f

        logger.info(
            f"Searching query='{query}' filters={filters_applied}"
        )

        embeddings = get_embeddings()
        query_vector = embeddings.embed_query(query)

        search_kwargs = {
            "near_vector": query_vector,
            "limit": limit,
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

        return {
            "results": results,
            "total": len(results),
            "query": query,
            "filters_applied": filters_applied,
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
    app = mcp.http_app()
    port = int(os.getenv("MCP_SERVER_PORT"))

    if not port:
        raise RuntimeError("MCP_SERVER_PORT env var required.")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
