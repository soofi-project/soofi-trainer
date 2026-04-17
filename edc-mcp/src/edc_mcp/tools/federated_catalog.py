"""
MCP tools for the Federated Catalog with SPARQL querying.

The catalog is automatically refreshed in the background.
Refresh interval is configured via CATALOG_REFRESH_INTERVAL environment variable (default: 300 seconds).
"""

from fastmcp import FastMCP
from edc_mcp.api.federated_catalog import (
    sparql_query,
    get_graph_stats
)


def register_federated_catalog_tools(mcp: FastMCP):
    """Register all federated catalog tools with the MCP server"""

    @mcp.tool()
    async def query_federated_catalog_sparql(query: str, format: str = "json") -> dict:
        """Execute a SPARQL query against the federated catalog RDF graph.

        The federated catalog aggregates datasets from multiple providers into a single
        queryable RDF graph. Use standard SPARQL 1.1 query syntax.

        Common prefixes available:
        - dcat: http://www.w3.org/ns/dcat#
        - dcterms: http://purl.org/dc/terms/
        - odrl: http://www.w3.org/ns/odrl/2/
        - dspace: https://w3id.org/dspace/v0.8/
        - edc: https://w3id.org/edc/v0.0.1/ns/

        Args:
            query (str): SPARQL SELECT or CONSTRUCT query
            format (str): Output format - json, xml, csv, or turtle (default: json)

        Returns:
            dict with:
            - _source: always "edc" — all datasets in this catalog originate from the EDC dataspace
            - results: query results in the specified format (string)

        Example to query datasets:
            query_federated_catalog_sparql('''
                PREFIX dcat: <http://www.w3.org/ns/dcat#>
                PREFIX dcterms: <http://purl.org/dc/terms/>                
                PREFIX edc: <https://w3id.org/edc/v0.0.1/ns/>
                PREFIX dspace: <https://w3id.org/dspace/v0.8/>

                SELECT ?id ?title ?participantId ?counterPartyAddress
                WHERE {
                    ?dataset a dcat:Dataset .
                    ?dataset edc:id ?id .
                    ?dataset dcterms:title ?title .
                    ?catalog dspace:participantId ?participantId .
                    ?catalog edc:originator ?counterPartyAddress .
                }
                LIMIT 10
            ''')
        """
        return {
            "_source": "edc",
            "results": await sparql_query(query, format),
        }

    @mcp.tool()
    async def get_federated_catalog_stats() -> dict:
        """Get statistics about the federated catalog graph.

        The catalog is automatically refreshed in the background.

        Returns:
            dict: Statistics including total triples, named graphs, and federated catalog triples
        """
        return get_graph_stats()

    @mcp.tool()
    async def get_federated_catalog_example_queries() -> dict:
        """Get example SPARQL queries for the federated catalog.

        Returns:
            dict: Dictionary of example queries with descriptions
        """
        return {
            "list_all_datasets": {
                "description": "List all datasets with their titles, participant ID and counterparty address",
                "query": """
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX dspace: <https://w3id.org/dspace/v0.8/>
PREFIX edc: <https://w3id.org/edc/v0.0.1/ns/>

SELECT ?id ?title ?participantId ?counterPartyAddress
WHERE {
    ?catalog dcat:dataset ?dataset .
    ?catalog dspace:participantId ?participantId .
    ?catalog edc:originator ?counterPartyAddress .
    ?dataset edc:id ?id .
    OPTIONAL { ?dataset dcterms:title ?title . }
}
LIMIT 100
"""
            },
            "search_by_keyword": {
                "description": "Search datasets by keyword in title or description",
                "query": """
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX dspace: <https://w3id.org/dspace/v0.8/>
PREFIX edc: <https://w3id.org/edc/v0.0.1/ns/>

SELECT ?dataset ?title ?description ?participantId ?counterPartyAddress
WHERE {
    ?catalog dcat:dataset ?dataset .
    ?catalog dspace:participantId ?participantId .
    ?catalog edc:originator ?counterPartyAddress .
    ?dataset edc:id ?id .
    OPTIONAL { ?dataset dcterms:title ?title . }
    OPTIONAL { ?dataset dcterms:description ?description . }
    FILTER (
        (BOUND(?title) && CONTAINS(LCASE(STR(?title)), "energy")) ||
        (BOUND(?description) && CONTAINS(LCASE(STR(?description)), "energy"))
    )
}
"""
            },
            "count_datasets": {
                "description": "Count total number of datasets",
                "query": """
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dspace: <https://w3id.org/dspace/v0.8/>
PREFIX edc: <https://w3id.org/edc/v0.0.1/ns/>

SELECT (COUNT(?dataset) as ?count)
WHERE {
    ?catalog dcat:dataset ?dataset .
    ?catalog dspace:participantId ?participantId .
    ?catalog edc:originator ?counterPartyAddress .
    ?dataset edc:id ?id .
}
"""
            },
            "datasets_with_policies": {
                "description": "Find datasets and their access policies",
                "query": """
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX odrl: <http://www.w3.org/ns/odrl/2/>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX dspace: <https://w3id.org/dspace/v0.8/>
PREFIX edc: <https://w3id.org/edc/v0.0.1/ns/>

SELECT ?dataset ?title ?policy ?participantId ?counterPartyAddress
WHERE {
    ?catalog dcat:dataset ?dataset .
    ?catalog dspace:participantId ?participantId .
    ?catalog edc:originator ?counterPartyAddress .
    OPTIONAL { ?dataset dcterms:title ?title . }
    ?dataset odrl:hasPolicy ?policy .
}
"""
            },
            "datasets_with_distributions": {
                "description": "Find datasets and their data distributions",
                "query": """
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX dspace: <https://w3id.org/dspace/v0.8/>
PREFIX edc: <https://w3id.org/edc/v0.0.1/ns/>

SELECT ?dataset ?title ?distribution ?format ?participantId ?counterPartyAddress
WHERE {
    ?catalog dcat:dataset ?dataset .
    ?catalog dspace:participantId ?participantId .
    ?catalog edc:originator ?counterPartyAddress .
    OPTIONAL { ?dataset dcterms:title ?title . }
    ?dataset dcat:distribution ?distribution .
    OPTIONAL { ?distribution dcterms:format ?format . }
}
"""
            }
        }
