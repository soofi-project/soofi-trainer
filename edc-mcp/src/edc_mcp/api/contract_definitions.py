from edc_mcp.client import management_api_client


async def list_contract_definitions(filter_expressions: list[dict] = None) -> list[dict]:
    """Return all contract definitions according to a query from the EDC Management API"""
    query_spec = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        },
        "@type": "QuerySpec",
        "offset": 0,
        "limit": 1000
    }

    if filter_expressions:
        query_spec["filterExpression"] = filter_expressions

    response = await management_api_client.post("/v3/contractdefinitions/request", json=query_spec)
    response.raise_for_status()

    return response.json()


async def get_contract_definition(id: str) -> dict:
    """Return a contract definition by ID from the EDC Management API"""
    response = await management_api_client.get(f"/v3/contractdefinitions/{id}")
    response.raise_for_status()

    return response.json()


async def delete_contract_definition(id: str) -> str:
    """Delete a contract definition by ID from the EDC Management API"""
    response = await management_api_client.delete(f"/v3/contractdefinitions/{id}")
    response.raise_for_status()
    return f"Contract definition {id} deleted successfully."


async def create_contract_definition(
    contract_policy_id: str,
    access_policy_id: str,
    assets_selector: list[dict],
    private_properties: dict | None = None
) -> dict:
    """Create a new contract definition in the EDC Management API

    Args:
        contract_policy_id: ID of the contract policy
        access_policy_id: ID of the access policy
        assets_selector: List of criterion dicts for asset selection
        private_properties: Optional private properties dict
    """
    contract_definition = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
            "edc": "https://w3id.org/edc/v0.0.1/ns/",
            "odrl": "http://www.w3.org/ns/odrl/2/"
        },
        "@type": "ContractDefinition",
        "accessPolicyId": access_policy_id,
        "contractPolicyId": contract_policy_id,
        "assetsSelector": assets_selector
    }

    if private_properties:
        contract_definition["privateProperties"] = private_properties

    response = await management_api_client.post("/v3/contractdefinitions", json=contract_definition)
    response.raise_for_status()

    return response.json()