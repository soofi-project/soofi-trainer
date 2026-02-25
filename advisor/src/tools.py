"""MCP client for the Vector MCP server."""

import os

from langchain_mcp_adapters.client import MultiServerMCPClient

VECTOR_MCP_URL = os.getenv("VECTOR_MCP_URL")
if not VECTOR_MCP_URL:
    raise RuntimeError("VECTOR_MCP_URL env var required.")

mcp_client = MultiServerMCPClient(
    {
        "knowledge": {
            "transport": "http",
            "url": VECTOR_MCP_URL,
        },
    }
)
