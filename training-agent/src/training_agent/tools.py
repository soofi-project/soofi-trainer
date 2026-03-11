"""MCP client for the Training Gateway."""

import os

from langchain_mcp_adapters.client import MultiServerMCPClient

TRAINING_GATEWAY_MCP_URL = os.getenv("TRAINING_GATEWAY_MCP_URL")
if not TRAINING_GATEWAY_MCP_URL:
    raise RuntimeError("TRAINING_GATEWAY_MCP_URL env var required.")

mcp_client = MultiServerMCPClient(
    {
        "training": {
            "transport": "http",
            "url": TRAINING_GATEWAY_MCP_URL,
        },
    }
)
