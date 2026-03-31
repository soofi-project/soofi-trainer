from pyld import jsonld
from edc_mcp.client import management_api_client
from typing import List


dataset_compaction_context = {
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
        "skos": "http://www.w3.org/2004/02/skos/core",
        "dspace": "https://w3id.org/dspace/v0.8/",
        "dcat:distribution": {
            "@id": "dcat:distribution",
            "@container": "@set",
        },
        "odrl:hasPolicy": {
            "@id": "odrl:hasPolicy",
            "@container": "@set",
            "@context": {
                "@vocab": "http://www.w3.org/ns/odrl/2/"
            }
        }
    }
}


async def get_dataset_from_catalog(counter_party_address: str, dataset_id: str) -> dict:
    """Return a dataset by ID from the EDC Management API catalog.

    Args:
        counter_party_address (str): The address of the counter party like "http://counter-party:19194/protocol"
        dataset_id (str): The dataset ID
    """

    dataset_request = {
         "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        },
        "@type": "DatasetRequest",
        "@id": dataset_id,
        "counterPartyAddress": counter_party_address,
        "protocol": "dataspace-protocol-http"
    }


    response = await management_api_client.post(f"/v3/catalog/dataset/request", json=dataset_request)
    response.raise_for_status()
    dataset = response.json()

    return jsonld.compact(dataset, dataset_compaction_context)
    


async def get_policies_for_dataset(counter_party_address: str, dataset_id: str) -> List[dict]:
    """Return the policies for a dataset by ID from the EDC Management API catalog.

    Args:
        counter_party_address (str): The address of the counter party like "http://counter-party:19194/protocol"
        dataset_id (str): The unique dataset id

    Returns:
        List[dict]: The list of policies associated with the dataset
    """
    dataset = await get_dataset_from_catalog(counter_party_address, dataset_id)
    return dataset['odrl:hasPolicy']


async def get_policy_for_dataset(counter_party_address: str, dataset_id: str, policy_id: str) -> dict:
    """Return a specific policy for a dataset by ID from the EDC Management API catalog.

    Args:
        counter_party_address (str): The address of the counter party like "http://counter-party:19194/protocol"
        dataset_id (str): The unique dataset id
        policy_id (str): The policy ID to retrieve

    Returns:
        dict: The policy associated with the dataset
    """
    dataset = await get_dataset_from_catalog(counter_party_address, dataset_id)
    
    # Policy IDs have format id1:id2:id3, only first two segments need to match
    policy_prefix = ':'.join(policy_id.split(':')[:2])
    
    for policy in dataset['odrl:hasPolicy']:
        policy_full_id = policy.get('@id', '')
        policy_full_prefix = ':'.join(policy_full_id.split(':')[:2])
        if policy_full_prefix == policy_prefix:
            return policy

    raise ValueError(f"Policy with ID prefix '{policy_prefix}' not found for dataset '{dataset_id}'")
