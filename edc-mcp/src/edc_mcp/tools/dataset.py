from fastmcp import FastMCP
from typing import List
from pyld import jsonld
from edc_mcp.api.dataset import (
    get_dataset_from_catalog as api_get_dataset_from_catalog,
    get_policies_for_dataset as api_get_policies_for_dataset,
    get_policy_for_dataset as api_get_policy_for_dataset
)


def register_dataset_tools(mcp: FastMCP):
    """Register all dataset-related tools with the MCP server"""

    @mcp.tool()
    async def get_policies_for_dataset(counter_party_address: str, dataset_id: str) -> List[dict]:
        """Return the policies for a dataset by ID from the EDC Management API catalog.

        Args:
            counter_party_address (str): The address of the counter party like "http://counter-party:19194/protocol"
            dataset_id (str): The unique dataset id

        Returns:
            List[dict]: The list of policies associated with the dataset containing the policy details and ids
        """
        return await api_get_policies_for_dataset(counter_party_address, dataset_id)

    @mcp.tool()
    async def get_policy_for_dataset(counter_party_address: str, dataset_id: str, policy_id: str) -> dict:
        """Return a specific policy for a dataset by ID from the EDC Management API catalog.

        Args:
            counter_party_address (str): The address of the counter party like "http://counter-party:19194/protocol"
            dataset_id (str): The unique dataset id
            policy_id (str): The policy ID to retrieve

        Returns:
            dict: The policy associated with the dataset
        """
        return await api_get_policy_for_dataset(counter_party_address, dataset_id, policy_id)

    @mcp.tool()
    async def get_dataset_from_catalog(counter_party_address: str, dataset_id: str) -> dict:
        """Return a dataset by ID from the EDC Management API catalog.

        Args:
            counter_party_address (str): The address of the counter party like "http://counter-party:19194/protocol"
            dataset_id (str): The unique dataset id
        Returns:
            Dataset: The dataset object
            - _source: always "edc" — use this as the dataset source when referencing for training
            - _uri: the dataset_id, use as URI when referencing this dataset for training
        """
        result = await api_get_dataset_from_catalog(counter_party_address, dataset_id)
        result["_source"] = "edc"
        result["_uri"] = dataset_id
        return result

    @mcp.tool()
    async def get_thing_description_for_dataset(counter_party_address: str, dataset_id: str) -> dict:
        """Return the Thing Description for a dataset by ID from the EDC Management API catalog. The thing description
        describes how to interact with a thing (service, device). A transfer process needs to be created to access the thing.

        Args:
            counter_party_address (str): The address of the counter party like "http://counter-party:19194/protocol"
            dataset_id (str): The unique dataset id
        Returns:
            dict: The Thing Description associated with the dataset
        """
        dataset = await api_get_dataset_from_catalog(counter_party_address, dataset_id)

        if dataset["https://www.w3.org/2019/wot/td#hasThingDescription"] is False:
            raise ValueError(
                f"No Thing Description available for dataset ID {dataset_id}")

        return jsonld.compact(
            dataset["https://www.w3.org/2019/wot/td#hasThingDescription"],
            {"@context": "https://www.w3.org/2022/wot/td/v1.1"}
        )
