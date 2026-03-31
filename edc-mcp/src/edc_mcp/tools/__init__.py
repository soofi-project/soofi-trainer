from .assets import register_asset_tools
from .policy_definitions import register_policy_tools
from .catalog import register_catalog_tools
from .contract_negotiations import register_contract_negotiation_tools
from .contract_agreement import register_contract_agreement_tools
from .dataset import register_dataset_tools
from .transfer_processes import register_transfer_process_tools
from .contract_definitions import register_contract_definition_tools
from .federated_catalog import register_federated_catalog_tools

__all__ = [
    "register_asset_tools",
    "register_policy_tools",
    "register_catalog_tools",
    "register_contract_negotiation_tools",
    "register_contract_agreement_tools",
    "register_dataset_tools",
    "register_transfer_process_tools",
    "register_contract_definition_tools",
    "register_federated_catalog_tools",
]


def register_tools(mcp):
    """Register all tools with the MCP server"""
    register_asset_tools(mcp)
    register_policy_tools(mcp)
    register_catalog_tools(mcp)
    register_contract_negotiation_tools(mcp)
    register_contract_agreement_tools(mcp)
    register_dataset_tools(mcp)
    register_transfer_process_tools(mcp)
    register_contract_definition_tools(mcp)
    register_federated_catalog_tools(mcp)
