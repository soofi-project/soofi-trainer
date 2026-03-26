from edc_mcp.client import management_api_client


async def list_contract_agreements() -> list[dict]:
    """Return all contract agreements according to a query from the EDC Management API"""
    query_spec = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        },
        "@type": "QuerySpec",
        "offset": 0,
        "limit": 1000
    }

    response = await management_api_client.post("/v3/contractagreements/request", json=query_spec)
    response.raise_for_status()

    return response.json()


async def get_contract_agreement(agreement_id: str) -> dict:
    """Get a specific contract agreement by ID according to the EDC Management API"""
    response = await management_api_client.get(f"/v3/contractagreements/{agreement_id}")
    response.raise_for_status()

    return response.json()


async def get_contract_agreement_by_negotiation(negotiation_id: str) -> dict:
    """Get the contract agreement for a specific contract negotiation by ID according to the EDC Management API"""
    response = await management_api_client.get(f"/v3/contractnegotiations/{negotiation_id}/agreement")
    response.raise_for_status()

    return response.json()