# pyright: reportUnusedFunction=false
from edc_mcp.client import management_api_client
from typing import List, Optional

asset_context = {
    "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
    "edc": "https://w3id.org/edc/v0.0.1/ns/",
    "dct": "http://purl.org/dc/terms/",
    "dcat": "http://www.w3.org/ns/dcat#",
    "prov": "http://www.w3.org/ns/prov#",
    "odrl": "http://www.w3.org/ns/odrl/2/",
    "dqv": "http://www.w3.org/ns/dqv#",
    "td": "https://www.w3.org/2019/wot/td#",
    "dpv": "https://w3id.org/dpv#",
    "schema": "http://schema.org/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
}


async def create_asset(
    properties: dict,
    data_address: dict,
    private_properties: Optional[dict] = None
) -> dict:
    """Create an asset in the EDC Management API

    Args:
        properties: Asset properties (metadata) as a dict
        data_address: Data address configuration as a dict
        private_properties: Optional private properties as a dict
    """
    asset = {
        "@context": asset_context,
        "@type": "Asset",
        "properties": properties,
        "dataAddress": data_address
    }

    if private_properties:
        asset["privateProperties"] = private_properties

    response = await management_api_client.post("/v3/assets", json=asset)
    response.raise_for_status()

    return response.json()


async def list_assets(filter_expressions: list[dict] = None, offset: int = 0, limit: int = 10) -> List[dict]:
    """Return all assets according to a query from the EDC Management API"""
    query_spec = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        },
        "@type": "QuerySpec",
        "offset": offset,
        "limit": limit
    }

    if filter_expressions:
        query_spec["filterExpression"] = filter_expressions

    response = await management_api_client.post("/v3/assets/request", json=query_spec)
    response.raise_for_status()

    return response.json()


async def get_asset(id: str) -> dict:
    """Return an asset by ID from the EDC Management API"""
    response = await management_api_client.get(f"/v3/assets/{id}")
    response.raise_for_status()

    return response.json()


async def delete_asset(id: str) -> str:
    """Delete an asset by ID from the EDC Management API

    Args:
        id: The unique identifier of the asset to delete
    """
    response = await management_api_client.delete(f"/v3/assets/{id}")
    response.raise_for_status()
    return f"Asset {id} deleted successfully."


async def update_asset_properties(id: str, properties: dict) -> dict:
    """Update an asset's properties

    Args:
        id: Asset ID
        properties: Properties dict to merge with existing properties
    """
    existing = await get_asset(id)
    existing_props = existing.get('properties', {})
    existing_data_addr = existing.get('dataAddress', {})
    existing_private_props = existing.get('privateProperties', {})

    # Merge new properties with existing
    updated_props = {**existing_props, **properties}

    asset = {
        "@context": asset_context,
        "@type": "Asset",
        "@id": id,
        "properties": updated_props,
        "dataAddress": existing_data_addr
    }

    if existing_private_props:
        asset["privateProperties"] = existing_private_props

    response = await management_api_client.put(f"/v3/assets", json=asset)
    response.raise_for_status()

    return {"@id": id}


async def update_asset_private_properties(id: str, private_properties: dict) -> dict:
    """Update an asset's private properties

    Args:
        id: Asset ID
        private_properties: Private properties dict to merge with existing private properties
    """
    existing = await get_asset(id)
    existing_props = existing.get('properties', {})
    existing_data_addr = existing.get('dataAddress', {})
    existing_private_props = existing.get('privateProperties', {})

    # Merge new private properties with existing
    updated_private_props = {**existing_private_props, **private_properties}

    asset = {
        "@context": asset_context,
        "@type": "Asset",
        "@id": id,
        "properties": existing_props,
        "dataAddress": existing_data_addr,
        "privateProperties": updated_private_props
    }

    response = await management_api_client.put(f"/v3/assets", json=asset)
    response.raise_for_status()

    return {"@id": id}


async def update_asset_data_address(id: str, data_address: dict) -> dict:
    """Update an asset's data address

    Args:
        id: Asset ID
        data_address: Data address dict to merge with existing data address
    """
    existing = await get_asset(id)
    existing_props = existing.get('properties', {})
    existing_data_addr = existing.get('dataAddress', {})
    existing_private_props = existing.get('privateProperties', {})

    # Merge new data address with existing
    updated_data_addr = {**existing_data_addr, **data_address}

    asset = {
        "@context": asset_context,
        "@type": "Asset",
        "@id": id,
        "properties": existing_props,
        "dataAddress": updated_data_addr
    }

    if existing_private_props:
        asset["privateProperties"] = existing_private_props

    response = await management_api_client.put(f"/v3/assets", json=asset)
    response.raise_for_status()

    return {"@id": id}
