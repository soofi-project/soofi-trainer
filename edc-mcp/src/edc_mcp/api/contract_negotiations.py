from edc_mcp.client import management_api_client
from typing import List


async def list_contract_negotiations() -> List[dict]:
    """Return all contract negotiations according to a query from the EDC Management API"""
    query_spec = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        },
        "@type": "QuerySpec",
        "offset": 0,
        "limit": 1000
    }

    response = await management_api_client.post("/v3/contractnegotiations/request", json=query_spec)
    response.raise_for_status()

    return response.json()


async def get_contract_negotiation(negotiation_id: str) -> dict:
    """Get a specific contract negotiation by ID according to the EDC Management API"""
    response = await management_api_client.get(f"/v3/contractnegotiations/{negotiation_id}")
    response.raise_for_status()

    return response.json()


async def get_contract_negotiation_by_agreement(agreement_id: str) -> dict:
    """Get the contract negotiation for a specific contract agreement by ID according to the EDC Management API"""
    response = await management_api_client.get(f"/v3/contractagreements/{agreement_id}/negotiation")
    response.raise_for_status()

    return response.json()


async def create_contract_negotiation(counter_party_address: str, policy: dict) -> dict:
    """Create a new contract negotiation according to the EDC Management API.

    Args:
        counter_party_address: The address of the counter party EDC connector
        policy: The policy to be used for the contract negotiation
    """
    contract_request = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
            "edc": "https://w3id.org/edc/v0.0.1/ns/",
        },
        "@type": "ContractRequest",
        "counterPartyAddress": counter_party_address,
        "protocol": "dataspace-protocol-http",
        "policy": policy
    }

    response = await management_api_client.post("/v3/contractnegotiations", json=contract_request)
    response.raise_for_status()

    return response.json()
