# Task

- user story: #US-04

/label ~UserStory_US-04
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**HuggingFace MCP Server Endpoint**

Implement an MCP server endpoint for searching datasets on HuggingFace Hub.

## Endpoint: `search_huggingface_datasets`

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Search term for dataset search |
| domain | string | No | Filter by domain (medical, legal, code, finance, etc.) |
| task | string | No | Filter by task (question-answering, summarization, classification, ner, text-generation, etc.) |
| language | string | No | Language filter (de, en, multi, etc.) |
| license | string | No | License filter (permissive, copyleft, research-only, commercial) |
| min_size | integer | No | Minimum dataset size (number of samples) |
| max_size | integer | No | Maximum dataset size |
| limit | integer | No | Max number of results (default: 10) |

### Response Fields per Dataset

| Field | Description |
|-------|-------------|
| name | Dataset identifier |
| author | Dataset author |
| description | Short description |
| size | Number of samples (train/validation/total) |
| license | License type |
| languages | Supported languages |
| tasks | Associated tasks |
| downloads | Download count |
| likes | Like count |
| url | HuggingFace URL |
| last_modified | Last modification date |

## License Mapping

| Filter Value | Included Licenses |
|--------------|-------------------|
| permissive | MIT, Apache-2.0, BSD-*, CC-BY, CC0, Unlicense |
| copyleft | GPL-*, LGPL-*, AGPL-*, CC-BY-SA |
| research-only | Research-only, Non-commercial, Academic |
| commercial | MIT, Apache-2.0, BSD-*, CC0 |

## Task Mapping

| Soofi Task | HuggingFace Task Tags |
|------------|----------------------|
| question-answering | question-answering, extractive-qa, open-domain-qa |
| summarization | summarization, text2text-generation |
| classification | text-classification, sentiment-analysis |
| ner | token-classification, named-entity-recognition |
| text-generation | text-generation, language-modeling |
| translation | translation, machine-translation |

## Requirements

- Results sorted by downloads (descending) by default
- Rate limiting for HuggingFace API must be respected
- Runs as a **separate Docker container** in the stack (independent from other MCP servers)

## Acceptance Criteria

- [ ] MCP server endpoint is implemented
- [ ] Search by query works
- [ ] Filtering by task, language, and license works
- [ ] Response contains all relevant fields
- [ ] Results are sorted by downloads
- [ ] Rate limiting is respected
- [ ] Runs as a Docker container

# Branches

- feature/US-04-dataset-search
