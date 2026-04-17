from fastmcp import FastMCP
from typing import List
from edc_mcp.api.catalog import (
    get_catalog as api_get_catalog
)


def register_catalog_tools(mcp: FastMCP):
    """Register all catalog-related tools with the MCP server"""

    @mcp.tool()
    async def get_catalog(counter_party_address: str, offset: int = 0, limit: int = 10) -> dict:
        """Return the data catalog from the EDC Management API.
        Args:
            counter_party_address (str): The address of the counter party like "http://counter-party:19194/protocol"
            offset (int): The offset for pagination
            limit (int): The limit for pagination
        Returns:
            Catalog: The data catalog
            - _source: always "edc" — use this as the dataset source when referencing for training
            - policies: List of policies in the catalog (do not truncate or modify ids)
        """
        result = await api_get_catalog(counter_party_address, offset=offset, limit=limit)
        result["_source"] = "edc"
        return result
