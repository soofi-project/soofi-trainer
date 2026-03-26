from fastmcp import FastMCP
from typing import List
from edc_mcp.api.contract_agreement import (
    list_contract_agreements as api_list_contract_agreements,
    get_contract_agreement as api_get_contract_agreement,
    get_contract_agreement_by_negotiation as api_get_contract_agreement_by_negotiation
)

def register_contract_agreement_tools(mcp: FastMCP):
    """Register all contract agreement-related tools with the MCP server"""

    @mcp.tool()
    async def get_contract_agreement(agreement_id: str) -> dict:
        """Get a specific contract agreement by ID according to the EDC Management API"""
        return await api_get_contract_agreement(agreement_id)

    @mcp.tool()
    async def get_contract_agreement_by_negotiation(negotiation_id: str) -> dict:
        """Get the contract agreement for a specific contract negotiation by ID according to the EDC Management API"""
        return await api_get_contract_agreement_by_negotiation(negotiation_id)

    @mcp.tool()
    async def list_contract_agreements() -> List[dict]:
        """Return all contract agreements according to a query from the EDC Management API"""
        return await api_list_contract_agreements()