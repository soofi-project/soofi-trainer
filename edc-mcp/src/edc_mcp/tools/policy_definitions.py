from fastmcp import FastMCP
from typing import List
from edc_mcp.api.policy_definitions import (
    list_policy_definitions as api_list_policy_definitions,
    get_policy_definition as api_get_policy_definition,
    delete_policy_definition as api_delete_policy_definition,
    create_policy_definition as api_create_policy_definition
)


def register_policy_tools(mcp: FastMCP):
    """Register all policy-related tools with the MCP server"""

    @mcp.tool()
    async def list_policy_definitions() -> List[dict]:
        """Return all policy definitions according to a query from the EDC Management API"""
        return await api_list_policy_definitions()

    @mcp.tool()
    async def get_policy_definition(id: str) -> dict:
        """Return a policy definition by ID from the EDC Management API"""
        return await api_get_policy_definition(id)

    @mcp.tool()
    async def delete_policy_definition(id: str) -> str:
        """Delete a policy definition by ID from the EDC Management API"""
        return await api_delete_policy_definition(id)

    @mcp.tool()
    async def create_policy_definition(policy: dict, private_properties: dict | None = None) -> dict:
        """Create a new policy definition in the EDC Management API
        Args:
            policy: The ODRL policy dict (e.g., {"@type": "odrl:Set", "odrl:permission": [...]})
            private_properties: Optional private properties dict (e.g., {"name": "My Policy"})
        Returns:
            dict: The created policy definition object
        """
        return await api_create_policy_definition(policy=policy, private_properties=private_properties)
