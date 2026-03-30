"""Federated Catalog API with RDF storage and SPARQL querying."""

import asyncio
import json
import logging
import os
import re
from typing import Optional, Any
from urllib.parse import quote

from rdflib import Dataset, URIRef
from edc_mcp.client import catalog_api_client

logger = logging.getLogger(__name__)

_graph: Optional[Dataset] = None
_background_task: Optional[asyncio.Task] = None
_catalog_query_interval: int = int(os.getenv("CATALOG_REFRESH_INTERVAL", "300"))
FEDERATED_CATALOG_GRAPH = URIRef("urn:federated:catalog")


def get_graph() -> Dataset:
    """Get or create the global RDF graph instance."""
    global _graph
    if _graph is None:
        try:
            _graph = Dataset(store="Oxigraph")
            logger.info("Initialized Oxigraph-backed Dataset (in-memory)")
        except Exception as e:
            logger.warning(
                f"Failed to initialize Oxigraph store: {e}. Falling back to default store."
            )
            _graph = Dataset()
    return _graph


async def query_catalog() -> Optional[dict]:
    """Query the federated catalog endpoint."""
    try:
        response = await catalog_api_client.post("/v1alpha/catalog/query")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to query federated catalog: {e}")
        return None


def sanitize_jsonld_iris(obj: Any) -> Any:
    """Recursively sanitize JSON-LD data to URL-encode invalid IRI characters."""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if isinstance(key, str) and (key.startswith("http://") or key.startswith("https://")):
                if re.search(r'[\^$\[\]{}|\\<>"]', key):
                    if "#" in key:
                        base, fragment = key.rsplit("#", 1)
                        fragment_encoded = re.sub(
                            r"([\^$\[\]{}|\\])", lambda m: quote(m.group(1)), fragment
                        )
                        key = f"{base}#{fragment_encoded}"

            result[key] = sanitize_jsonld_iris(value)
        return result
    elif isinstance(obj, list):
        return [sanitize_jsonld_iris(item) for item in obj]
    elif isinstance(obj, str):
        if (obj.startswith("http://") or obj.startswith("https://")) and re.search(
            r'[\^$\[\]{}|\\<>"]', obj
        ):
            if "#" in obj:
                base, fragment = obj.rsplit("#", 1)
                fragment_encoded = re.sub(
                    r"([\^$\[\]{}|\\])", lambda m: quote(m.group(1)), fragment
                )
                return f"{base}#{fragment_encoded}"
        return obj
    else:
        return obj


def load_catalog_to_graph(jsonld_data: dict) -> None:
    """Load a catalog JSON-LD document into the federated catalog graph."""
    graph = get_graph()
    federated_graph = graph.get_context(FEDERATED_CATALOG_GRAPH)
    federated_graph.remove((None, None, None))

    try:
        sanitized_data = sanitize_jsonld_iris(jsonld_data)
        base_uri = os.getenv("CATALOG_BASE_URI", "urn:edc:catalog/")
        jsonld_bytes = json.dumps(sanitized_data).encode("utf-8")
        federated_graph.parse(data=jsonld_bytes, format="json-ld", publicID=base_uri)
        logger.info(f"Loaded catalog into graph {FEDERATED_CATALOG_GRAPH}")
    except Exception as e:
        logger.error(f"Failed to parse catalog JSON-LD: {e}")


async def refresh_catalog() -> bool:
    """Refresh the federated catalog."""
    logger.info("Querying federated catalog")
    catalog_data = await query_catalog()

    if catalog_data:
        load_catalog_to_graph(catalog_data)
        return True
    return False


async def periodic_catalog_refresh():
    """Background task that periodically refreshes the catalog."""
    logger.info(f"Starting periodic catalog refresh (interval: {_catalog_query_interval}s)")

    try:
        await refresh_catalog()
    except Exception as e:
        logger.error(f"Error in initial catalog sync: {e}")

    while True:
        await asyncio.sleep(_catalog_query_interval)
        try:
            await refresh_catalog()
        except Exception as e:
            logger.error(f"Error in periodic catalog refresh: {e}")


def start_background_refresh():
    """Start the background catalog refresh task on application startup."""
    global _background_task

    try:
        if _background_task is None or _background_task.done():
            _background_task = asyncio.create_task(periodic_catalog_refresh())
            logger.info(
                f"Started background catalog refresh task (interval: {_catalog_query_interval}s)"
            )
    except RuntimeError:
        logger.warning("Cannot start background refresh: no event loop running")


_SPARQL_WRITE_PATTERN = re.compile(r"\b(INSERT|DELETE|DROP|CREATE|CLEAR|LOAD)\b", re.IGNORECASE)


async def sparql_query(query: str, format: str = "json") -> str:
    """Execute a SPARQL query against the federated catalog graph.

    Only read-only queries (SELECT, ASK, DESCRIBE, CONSTRUCT) are allowed.
    """
    if _SPARQL_WRITE_PATTERN.search(query):
        raise ValueError(
            "Only read-only SPARQL queries are allowed (SELECT, ASK, DESCRIBE, CONSTRUCT). "
            "Write operations (INSERT, DELETE, DROP, CREATE, CLEAR, LOAD) are rejected."
        )

    graph = get_graph()
    federated_graph = graph.get_context(FEDERATED_CATALOG_GRAPH)

    try:
        results = federated_graph.query(query)
        if format.lower() == "json":
            return results.serialize(format="json")
        elif format.lower() == "xml":
            return results.serialize(format="xml")
        elif format.lower() == "csv":
            return results.serialize(format="csv")
        elif format.lower() == "turtle":
            return results.serialize(format="turtle")
        else:
            return results.serialize(format="json")
    except Exception as e:
        logger.error(f"SPARQL query failed: {e}")
        raise ValueError(f"SPARQL query execution failed: {e}")


def get_graph_stats() -> dict:
    """Get statistics about the federated catalog graph."""
    graph = get_graph()
    federated_graph = graph.get_context(FEDERATED_CATALOG_GRAPH)

    return {
        "total_triples": len(graph),
        "federated_catalog_triples": len(federated_graph),
        "named_graphs": len(list(graph.contexts())),
    }


def clear_graph():
    """Clear all data from the federated catalog graph."""
    graph = get_graph()
    for context in list(graph.contexts()):
        graph.remove_context(context)
    logger.info("Cleared federated catalog graph")
