from edc_mcp.client import management_api_client
from typing import List


async def list_policy_definitions() -> List[dict]:
    """Return all policy definitions according to a query from the EDC Management API"""
    query_spec = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        },
        "@type": "QuerySpec",
        "offset": 0,
        "limit": 1000
    }

    response = await management_api_client.post("/v3/policydefinitions/request", json=query_spec)
    response.raise_for_status()

    return response.json()


async def get_policy_definition(id: str) -> dict:
    """Return a policy definition by ID from the EDC Management API"""
    response = await management_api_client.get(f"/v3/policydefinitions/{id}")
    response.raise_for_status()

    return response.json()


async def delete_policy_definition(id: str) -> str:
    """Delete a policy definition by ID from the EDC Management API"""
    response = await management_api_client.delete(f"/v3/policydefinitions/{id}")
    response.raise_for_status()
    return f"Policy definition {id} deleted successfully."


async def create_policy_definition(policy: dict, private_properties: dict | None = None) -> dict:
    """Create a new policy definition in the EDC Management API

    Args:
        policy: The ODRL policy dict
        private_properties: Optional private properties dict
    """
    policy_definition = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
            "edc": "https://w3id.org/edc/v0.0.1/ns/",
            "odrl": "http://www.w3.org/ns/odrl/2/",
            "dct": "http://purl.org/dc/terms/"
        },
        "@type": "PolicyDefinition",
        "policy": policy
    }

    if private_properties:
        policy_definition["privateProperties"] = private_properties

    response = await management_api_client.post("/v3/policydefinitions", json=policy_definition)
    response.raise_for_status()

    return response.json()
