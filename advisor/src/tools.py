"""Load MCP tools from the Vector MCP server as LangChain tools."""

import os

from langchain_mcp_adapters.client import MultiServerMCPClient

VECTOR_MCP_URL = os.environ["VECTOR_MCP_URL"]

mcp_client = MultiServerMCPClient(
    {
        "knowledge": {
            "transport": "http",
            "url": VECTOR_MCP_URL,
        },
    }
)
