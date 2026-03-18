from fastmcp import FastMCP
from typing import List
import json
from edc_mcp.api.contract_negotiations import (
    list_contract_negotiations as api_list_contract_negotiations,
    get_contract_negotiation as api_get_contract_negotiation,
    get_contract_negotiation_by_agreement as api_get_contract_agreement_by_negotiation,
    create_contract_negotiation as api_create_contract_negotiation
)
from edc_mcp.api.dataset import get_policy_for_dataset


def register_contract_negotiation_tools(mcp: FastMCP):
    """Register all contract negotiation-related tools with the MCP server"""

    @mcp.tool()
    async def list_contract_negotiations() -> List[dict]:
        """Return all contract negotiations according to a query from the EDC Management API"""
        return await api_list_contract_negotiations()

    @mcp.tool()
    async def get_contract_negotiation(negotiation_id: str) -> dict:
        """Get a specific contract negotiation by ID according to the EDC Management API"""
        return await api_get_contract_negotiation(negotiation_id)

    @mcp.tool()
    async def get_contract_negotiation_by_agreement(agreement_id: str) -> dict:
        """Get the contract negotiation for a specific contract agreement by ID according to the EDC Management API"""
        return await api_get_contract_agreement_by_negotiation(agreement_id)

    @mcp.tool()
    async def create_contract_negotiation(
        counter_party_address: str,
        dataset_id: str,
        policy_id: str,
        participant_id: str
    ) -> dict:
        """Create a new contract negotiation according to the EDC Management API.

        Args:
            counter_party_address: The address of the counter party EDC connector
            dataset_id: The dataset id. Not the title or name, but the unique id of the dataset. In most cases this is a uuid.
            policy_id: The policy ID to be used for the contract negotiation.
            participant_id: The participant ID from the catalog.
        """

        # Fetch policy for dataset
        policy = await get_policy_for_dataset(counter_party_address, dataset_id, policy_id)

        # Add required fields to policy
        policy['assigner'] = participant_id
        policy['target'] = dataset_id
        policy['@context'] = "http://www.w3.org/ns/odrl.jsonld"

        print ("Creating contract negotiation with policy:", json.dumps(policy, indent=2))

        return await api_create_contract_negotiation(counter_party_address, policy)
