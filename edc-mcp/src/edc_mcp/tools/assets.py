from fastmcp import FastMCP
from typing import List, Optional
from edc_mcp.api.assets import (
    create_asset as api_create_asset,
    list_assets as api_list_assets,
    get_asset as api_get_asset,
    delete_asset as api_delete_asset,
    update_asset_properties as api_update_asset_properties,
    update_asset_private_properties as api_update_asset_private_properties,
    update_asset_data_address as api_update_asset_data_address
)


def register_asset_tools(mcp: FastMCP):
    """Register all asset-related tools with the MCP server"""

    @mcp.tool()
    async def create_asset(
        properties: dict,
        data_address: dict,
        private_properties: Optional[dict] = None
    ) -> dict:
        """Create an asset in the EDC Management API

        Args:
            properties: Asset properties (metadata) as a dict containing fields like title, description, keywords, etc.
            data_address: Data address configuration as a dict (e.g., {"type": "HttpData", "baseUrl": "...", "proxyPath": "true"})
            private_properties: Optional private properties as a dict
            
        """
        return await api_create_asset(
            properties=properties,
            data_address=data_address,
            private_properties=private_properties
        )

    @mcp.tool()
    async def list_assets(offset: int = 0, limit: int = 10) -> List[dict]:
        """Return all assets according to a query from the EDC Management API

        Args:
            offset (int): Number of items to skip before starting to collect the result set.
            limit (int): Maximum number of items to return.

        Returns:
            List[dict]: A list of asset objects as returned by the EDC Management API.
        """
        return await api_list_assets(offset=offset, limit=limit)

    @mcp.tool()
    async def find_assets(filter_expressions: List[dict], offset: int = 0, limit: int = 10) -> List[dict]:
        """Find and return assets by filter expressions from the EDC Management API

        Args:
            filter_expressions: List of filter expression dicts (e.g., [{"operandLeft": "properties.'http://purl.org/dc/terms/title'", "operator": "LIKE", "operandRight": "%keyword%"}])
            offset: Number of items to skip before starting to collect the result set
            limit: Maximum number of items to return

        Returns:
            List[dict]: List of asset objects matching the filter expressions
        """
        return await api_list_assets(filter_expressions=filter_expressions, offset=offset, limit=limit)

    @mcp.tool()
    async def get_asset(id: str) -> dict:
        """Return an asset by ID from the EDC Management API
        Args:
            id: The unique identifier of the asset to retrieve
        Returns:
            dict: The asset object
        """
        return await api_get_asset(id)

    @mcp.tool()
    async def delete_asset(id: str) -> str:
        """Delete an asset by ID from the EDC Management API

        Args:
            id: The unique identifier of the asset to delete
        Returns:
            str: Confirmation message upon successful deletion
        """
        return await api_delete_asset(id)

    @mcp.tool()
    async def update_asset_properties(id: str, properties: dict) -> dict:
        """Update an asset's properties in the EDC Management API

        Args:
            id: The unique identifier of the asset to update
            properties: Properties dict to merge with existing properties (e.g., {"dct:title": "New Title", "dcat:keyword": ["keyword1", "keyword2"]})
        Returns:
            dict: The response object after updating the asset (the asset ID)
        """
        return await api_update_asset_properties(id=id, properties=properties)

    @mcp.tool()
    async def update_asset_private_properties(id: str, private_properties: dict) -> dict:
        """Update an asset's private properties in the EDC Management API

        Args:
            id: The unique identifier of the asset to update
            private_properties: Private properties dict to merge with existing private properties
        Returns:
            dict: The response object after updating the asset (the asset ID)
        """
        return await api_update_asset_private_properties(id=id, private_properties=private_properties)

    @mcp.tool()
    async def update_asset_data_address(id: str, data_address: dict) -> dict:
        """Update an asset's data address in the EDC Management API

        Args:
            id: The unique identifier of the asset to update
            data_address: Data address dict to merge with existing data address (e.g., {"baseUrl": "http://new-url.com", "proxyPath": "true"})
        Returns:
            dict: The response object after updating the asset (the asset ID)
        """
        return await api_update_asset_data_address(id=id, data_address=data_address)
