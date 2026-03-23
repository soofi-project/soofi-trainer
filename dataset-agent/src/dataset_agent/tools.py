"""MCP client for dataset search across EDC and HuggingFace MCP servers."""

import os

from langchain_mcp_adapters.client import MultiServerMCPClient

EDC_MCP_URL = os.getenv("EDC_MCP_URL")
if not EDC_MCP_URL:
    raise RuntimeError("EDC_MCP_URL env var required.")

HUGGINGFACE_MCP_URL = os.getenv("HUGGINGFACE_MCP_URL")
if not HUGGINGFACE_MCP_URL:
    raise RuntimeError("HUGGINGFACE_MCP_URL env var required.")

mcp_client = MultiServerMCPClient(
    {
        "edc": {
            "transport": "http",
            "url": EDC_MCP_URL,
        },
        "huggingface": {
            "transport": "http",
            "url": HUGGINGFACE_MCP_URL,
        },
    }
)
