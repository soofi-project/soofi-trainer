from pyld import jsonld
from edc_mcp.client import management_api_client

catalog_compaction_context = {
    "@context": {
        "@vocab": "https://w3id.org/edc/v0.0.1/ns/",
        "edc": "https://w3id.org/edc/v0.0.1/ns/",
        "odrl": "http://www.w3.org/ns/odrl/2/",
        "dcat": "http://www.w3.org/ns/dcat#",
        "dct": "http://purl.org/dc/terms/",
        "prov": "http://www.w3.org/ns/prov#",
        "dpv": "https://w3id.org/dpv#",
        "dqv": "http://www.w3.org/ns/dqv#",
        "schema": "http://schema.org/",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "dspace": "https://w3id.org/dspace/v0.8/",
        "aas": "https://admin-shell.io/aas/3/0/",
    }
}


async def get_catalog(
    counter_party_address: str,
    filter_expressions: list[dict] = None,
    offset: int = 0,
    limit: int = 10,
) -> dict:
    catalog_request = {
        "@context": {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
        "@type": "CatalogRequest",
        "counterPartyAddress": counter_party_address,
        "protocol": "dataspace-protocol-http",
        "querySpec": {"offset": offset, "limit": limit},
    }

    if filter_expressions:
        catalog_request["querySpec"]["filterExpression"] = filter_expressions

    response = await management_api_client.post("/v3/catalog/request", json=catalog_request)
    response.raise_for_status()

    return jsonld.compact(response.json(), catalog_compaction_context)
