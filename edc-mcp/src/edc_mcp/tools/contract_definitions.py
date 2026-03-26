from fastmcp import FastMCP
from typing import List
from edc_mcp.api.contract_definitions import (
    create_contract_definition as api_create_contract_definition,
    list_contract_definitions as api_list_contract_definitions,
    get_contract_definition as api_get_contract_definition,
    delete_contract_definition as api_delete_contract_definition
)


def register_contract_definition_tools(mcp: FastMCP):
    """Register all contract definition-related tools with the MCP server"""

    @mcp.tool()
    async def list_contract_definitions() -> List[dict]:
        """Return all contract definitions according to a query from the EDC Management API"""
        return await api_list_contract_definitions()

    @mcp.tool()
    async def find_contract_definitions_by_name(name: str) -> List[dict]:
        """Find contract definitions by name from the EDC Management API
        Args:
            name: The name of the contract definitions to search for
        Returns:
            List[dict]: A list of contract definitions matching the name
        """
        filter_expressions = [
            {
                "operandLeft": "privateProperties.'https://w3id.org/edc/v0.0.1/ns/name'",
                "operator": "LIKE",
                "operandRight": f"%{name}%"
            }
        ]
        return await api_list_contract_definitions(filter_expressions=filter_expressions)


    @mcp.tool()
    async def create_contract_definition(
        contract_policy_id: str,
        access_policy_id: str,
        assets_selector: List[dict],
        private_properties: dict | None = None
    ) -> dict:
        """Create a new contract definition in the EDC Management API

        contract_policy_id and access_policy_id can be (and are in most cases) the same policy ID.

        Args:
            contract_policy_id: ID of the contract policy: this policy defines who can create a contract agreement
            access_policy_id: ID of the access policy. this policy defines who can see the asset(s) in the catalog
            assets_selector: List of criterion dicts for asset selection (e.g., [{"@type": "Criterion", "operandLeft": "https://w3id.org/edc/v0.0.1/ns/id", "operator": "in", "operandRight": ["asset-1", "asset-2"]}])
            private_properties: Optional private properties dict (e.g., {"name": "My Contract", "description": "Description"})
        Returns:
            dict: The created contract definition object
        """
        if not assets_selector:
            raise ValueError("assets_selector cannot be empty — please provide at least one criterion.")

        return await api_create_contract_definition(
            contract_policy_id=contract_policy_id,
            access_policy_id=access_policy_id,
            assets_selector=assets_selector,
            private_properties=private_properties
        )

    @mcp.tool()
    async def get_contract_definition(id: str) -> dict:
        """Return a contract definition by ID from the EDC Management API
        Args:
            id: The unique identifier of the contract definition to retrieve
        Returns:
            dict: The contract definition object
        """
        return await api_get_contract_definition(id)

    @mcp.tool()
    async def delete_contract_definition(id: str) -> str:
        """Delete a contract definition by ID from the EDC Management API
        Args:
            id: The unique identifier of the contract definition to delete
        Returns:
            str: Confirmation message upon successful deletion
        """
        return await api_delete_contract_definition(id)