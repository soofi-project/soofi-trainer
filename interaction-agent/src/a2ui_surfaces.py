"""A2UI surface definitions for the Soofi Interaction Agent."""

import os
from typing import Any

# ---------------------------------------------------------------------------
# Dashboard URLs (from environment, set via docker-compose / .env)
# ---------------------------------------------------------------------------

_mcp_port = os.getenv("MCPINSPECTOR_CLIENT_PORT")
if not _mcp_port:
    raise RuntimeError("MCPINSPECTOR_CLIENT_PORT env var required.")

_mcp_token = os.getenv("MCP_AUTH_TOKEN")
if not _mcp_token:
    raise RuntimeError("MCP_AUTH_TOKEN env var required.")

_n8n_port = os.getenv("N8N_EXTERNAL_PORT")
if not _n8n_port:
    raise RuntimeError("N8N_EXTERNAL_PORT env var required.")

MCP_INSPECTOR_URL = (
    f"http://localhost:{_mcp_port}"
    f"/?transport=streamable-http"
    f"&serverUrl=http://vector-mcp:8000/mcp"
    f"&MCP_PROXY_AUTH_TOKEN={_mcp_token}"
)
N8N_URL = f"http://localhost:{_n8n_port}"

# ---------------------------------------------------------------------------
# Dashboard descriptions
# ---------------------------------------------------------------------------

MCP_INSPECTOR_DESC = (
    "Der MCP Inspector zeigt die verfügbaren Semantic-Search-Tools "
    "(search_documents, list_metadata) und ermöglicht Testaufrufe "
    "gegen die Weaviate-Vektordatenbank."
)
N8N_DESC = (
    "N8N ist unsere visuelle Workflow-Automation-Plattform. "
    "Hier können Sie Verarbeitungs-Pipelines und "
    "Integrationen grafisch modellieren und ausführen."
)

# ---------------------------------------------------------------------------
# Surface builders
# ---------------------------------------------------------------------------


def _dashboard_surface(url: str, title: str, description: str) -> list[dict[str, Any]]:
    """Create an A2UI surface with a DashboardEmbed component (rendered as link card)."""
    return [
        {
            "surfaceUpdate": {
                "surfaceId": "main",
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "Column": {"children": {"explicitList": ["dash-card"]}}
                        },
                    },
                    {
                        "id": "dash-card",
                        "component": {"Card": {"child": "dash-embed"}},
                    },
                    {
                        "id": "dash-embed",
                        "component": {
                            "DashboardEmbed": {
                                "url": url,
                                "title": title,
                                "description": description,
                            }
                        },
                    },
                ],
            }
        },
        {"beginRendering": {"surfaceId": "main", "root": "root"}},
    ]


def mcp_inspector_surface() -> list[dict[str, Any]]:
    """A2UI surface for MCP Inspector dashboard link."""
    return _dashboard_surface(MCP_INSPECTOR_URL, "MCP Inspector", MCP_INSPECTOR_DESC)


def n8n_surface() -> list[dict[str, Any]]:
    """A2UI surface for N8N dashboard link."""
    return _dashboard_surface(N8N_URL, "N8N Workflows", N8N_DESC)
