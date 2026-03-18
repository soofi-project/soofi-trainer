from edc_mcp.client import management_api_client
from typing import List, Optional
import httpx


async def list_transfer_processes() -> List[dict]:
    """Return all transfer processes according to a query from the EDC Management API"""
    query_spec = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        },
        "@type": "QuerySpec",
        "offset": 0,
        "limit": 1000
    }

    response = await management_api_client.post("/v3/transferprocesses/request", json=query_spec)
    response.raise_for_status()

    return response.json()


async def get_transfer_process(transfer_process_id: str) -> dict:
    """Get a specific transfer process by ID according to the EDC Management API"""
    response = await management_api_client.get(f"/v3/transferprocesses/{transfer_process_id}")
    response.raise_for_status()

    return response.json()


async def create_transfer_process_http_pull(counter_party_address: str, contract_id: str) -> dict:
    """Create a new transfer process using the HTTP Pull transfer type according to the EDC Management API"""
    transfer_request = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        },
        "@type": "TransferRequestDto",
        "counterPartyAddress": counter_party_address,
        "contractId": contract_id,
        "protocol": "dataspace-protocol-http",
        "transferType": "HttpData-PULL"
    }

    response = await management_api_client.post("/v3/transferprocesses", json=transfer_request)
    response.raise_for_status()

    return response.json()


async def get_data_address_for_http_pull_transfer_process(transfer_process_id: str) -> dict:
    """Return a data address for HTTP Pull transfer type"""
    response = await management_api_client.get(f"/v3/edrs/{transfer_process_id}/dataaddress")
    response.raise_for_status()

    return response.json()

async def create_transfer_process_http_push(
    counter_party_address: str, 
    contract_id: str, 
    base_url: str,
    path: Optional[str] = None,
    method: Optional[str] = None,
    content_type: Optional[str] = None
) -> dict:
    """Create a new transfer process using the HTTP Push transfer type according to the EDC Management API"""
    transfer_request = {
        "@context": {
            "@vocab": "https://w3id.org/edc/v0.0.1/ns/"
        },
        "@type": "TransferRequestDto",
        "counterPartyAddress": counter_party_address,
        "contractId": contract_id,
        "protocol": "dataspace-protocol-http",
        "transferType": "HttpData-PUSH",
        "dataDestination": {
            "type": "HttpData",
            "baseUrl": base_url,
            "path": path,
            "method": method,
            "contentType": content_type,
        },
    }

    response = await management_api_client.post("/v3/transferprocesses", json=transfer_request)
    response.raise_for_status()

    return response.json()


async def perform_http_pull_request(
    transfer_process_id: str,
    path: Optional[str] = None,
    method: Optional[str] = "GET",
    content_type: Optional[str] = None,
    body: Optional[str] = None
) -> dict:
    """Perform HTTP pull request using the data address from a transfer process.

    This function first fetches the data address for the transfer process,
    then uses the endpoint and authorization information to make an HTTP request.

    Args:
        transfer_process_id (str): The ID of the transfer process
        path (Optional[str]): Additional path to append to the endpoint
        method (Optional[str]): HTTP method to use (default: "GET")
        content_type (Optional[str]): Content type for the request
        body (Optional[str]): Request body as a string (will be sent as-is)

    Returns:
        dict: Response containing status, headers, and data
    """

    data_address = await get_data_address_for_http_pull_transfer_process(transfer_process_id)

    endpoint = data_address.get("endpoint")
    authorization = data_address.get("authorization")

    if not endpoint:
        raise ValueError("No endpoint found in data address")

    url = endpoint
    if path:
        url = f"{endpoint.rstrip('/')}/{path.lstrip('/')}"

    headers = {}
    if authorization:
        headers["Authorization"] = f"{authorization}"
    if content_type:
        headers["Content-Type"] = content_type

    http_method = (method or "GET").upper()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                http_method,
                url,
                headers=headers,
                content=body if body else None
            )

            try:
                response_data = response.json()
            except:
                response_data = response.text

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": response_data,
                "url": url,
                "method": method
            }
        except httpx.RequestError as e:
            raise Exception(f"HTTP request failed: {str(e)}")
