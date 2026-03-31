import httpx
import os

EDC_MANAGEMENT_URL = os.getenv(
    "EDC_MANAGEMENT_URL", "http://localhost:5173/api/management")

EDC_CATALOG_URL = os.getenv(
    "EDC_CATALOG_URL", "http://localhost:5173/api/catalog")

management_api_client = httpx.AsyncClient(
    base_url=EDC_MANAGEMENT_URL,
    timeout=30.0
)

catalog_api_client = httpx.AsyncClient(
    base_url=EDC_CATALOG_URL,
    timeout=30.0
)