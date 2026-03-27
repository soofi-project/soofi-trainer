from fastmcp import FastMCP
from typing import List, Optional
from edc_mcp.api.transfer_processes import (
    list_transfer_processes as api_list_transfer_processes,
    create_transfer_process_http_pull as api_create_transfer_process_http_pull,
    get_data_address_for_http_pull_transfer_process as api_get_data_address_for_http_pull_transfer_process,
    get_transfer_process as api_get_transfer_process,
    create_transfer_process_http_push as api_create_transfer_process_http_push,
    perform_http_pull_request as api_perform_http_pull_request
)


def register_transfer_process_tools(mcp: FastMCP):
    """Register all transfer process-related tools with the MCP server"""

    @mcp.tool()
    async def list_transfer_processes() -> List[dict]:
        """Return all transfer processes according to a query from the EDC Management API"""
        return await api_list_transfer_processes()

    @mcp.tool()
    async def create_transfer_process_http_pull(counter_party_address: str, contract_id: str) -> dict:
        """Create a new transfer process using the HTTP Pull transfer type according to the EDC Management API.
        Args:
            counter_party_address (str): The address of the counter party EDC connector
            contract_id (str): The contract ID to be used for the transfer process
        Returns:
            dict: The created transfer process object
        """
        return await api_create_transfer_process_http_pull(counter_party_address, contract_id)

    @mcp.tool()
    async def create_transfer_process_http_push(
        counter_party_address: str,
        contract_id: str,
        base_url: str,
        path: Optional[str] = None,
        method: Optional[str] = "POST",
        content_type: Optional[str] = None
    ) -> dict:
        """Create a new transfer process using the HTTP Push transfer type according to the EDC Management API.
        Args:
            counter_party_address (str): The address of the counter party EDC connector
            contract_id (str): The contract ID to be used for the transfer process
            base_url (str): The base URL for the HTTP Push transfer
            path (Optional[str]): The path to append to the base URL
            method (Optional[str]): The HTTP method to use (default is "POST")
            content_type (Optional[str]): The content type for the HTTP Push transfer
        Returns:
            dict: The created transfer process object
        """
        return await api_create_transfer_process_http_push(
            counter_party_address,
            contract_id,
            base_url,
            path,
            method,
            content_type
        )

    @mcp.tool()
    async def get_transfer_process(transfer_process_id: str) -> dict:
        """Get a specific transfer process by ID according to the EDC Management API
        Args:
            transfer_process_id (str): The ID of the transfer process
        Returns:
            dict: The transfer process object
        """
        return await api_get_transfer_process(transfer_process_id)

    @mcp.tool()
    async def get_data_address_for_http_pull_transfer_process(transfer_process_id: str) -> dict:
        """Return a data address for HTTP Pull transfer type. 
        The data address contains the URL from which data can be pulled as well as any necessary authentication information.
        Args:
            transfer_process_id (str): The ID of the transfer process
        Returns:
            dict: The data address associated with the transfer process
        """
        return await api_get_data_address_for_http_pull_transfer_process(transfer_process_id)

    @mcp.tool()
    async def perform_http_pull_request(
        transfer_process_id: str,
        path: Optional[str] = None,
        method: Optional[str] = "GET",
        content_type: Optional[str] = None,
        body: Optional[str] = None
    ) -> dict:
        """Perform an HTTP pull request directly using a transfer process.

        This tool fetches the data address for the given transfer process and then
        performs an HTTP request to the endpoint with proper authentication.

        Args:
            transfer_process_id (str): The ID of the transfer process
            path (Optional[str]): Additional path to append to the endpoint URL
            method (Optional[str]): HTTP method to use (default: "GET")
            content_type (Optional[str]): Content type header for the request
            body (Optional[str]): Request body as a string (will be sent as-is)

        Returns:
            dict: Response containing status_code, headers, data, url, and method
        """
        return await api_perform_http_pull_request(transfer_process_id, path, method, content_type, body)
