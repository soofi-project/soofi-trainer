# Task

- user story: #US-04

/label ~UserStory_US-04
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Eclipse Dataspace MCP Server Endpoint**

Implement an MCP server endpoint for searching datasets in the Eclipse Dataspace ecosystem.

## Endpoint: `search_eclipse_dataspace`

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Search term for dataset search |
| domain | string | No | Filter by domain (medical, legal, code, finance, etc.) |
| task | string | No | Filter by task (question-answering, summarization, classification, etc.) |
| language | string | No | Language filter (de, en, multi, etc.) |
| license | string | No | License filter (permissive, copyleft, research-only, commercial) |
| limit | integer | No | Max number of results (default: 10) |

### Response Fields per Dataset

| Field | Description |
|-------|-------------|
| name | Dataset identifier |
| provider | Data provider / organization |
| description | Short description |
| size | Dataset size (if available) |
| license | License or usage policy |
| languages | Supported languages |
| tasks | Associated tasks |
| url | Link to the dataset or catalog entry |
| last_modified | Last modification date |

## Requirements

- Results sorted by relevance by default
- Runs as a **separate Docker container** in the stack (independent from other MCP servers)
- Handles authentication and connector protocols as required by Eclipse Dataspace

## Open Questions

- Which Eclipse Dataspace connector or catalog API to use (EDC, DAPS, Federated Catalog)?
- Authentication and access policies for data offers
- Mapping between Dataspace usage policies and license filter values

## Acceptance Criteria

- [ ] MCP server endpoint is implemented
- [ ] Search by query works
- [ ] Filtering by domain, task, and language works (where supported)
- [ ] Response contains all available fields
- [ ] Runs as a Docker container
- [ ] Error handling for unavailable connectors or catalogs

# Branches

- feature/US-04-dataset-search
