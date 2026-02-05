# Task

- user story: #US-05

/label ~UserStory_US-05
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**HuggingFace MCP Server Endpoint**

Implement an MCP server endpoint for searching datasets on HuggingFace.

## New MCP Server Endpoint: `search_huggingface_datasets`

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search term for dataset search |
| `domain` | string | No | Filter by domain (medical, legal, code, finance, etc.) |
| `task` | string | No | Filter by task (question-answering, summarization, classification, ner, text-generation, etc.) |
| `language` | string | No | Language filter (de, en, multi, etc.) |
| `license` | string | No | License filter (permissive, copyleft, research-only, etc.) |
| `min_size` | integer | No | Minimum dataset size (number of samples) |
| `max_size` | integer | No | Maximum dataset size |
| `limit` | integer | No | Max number of results (default: 10) |

### Response Format

```json
{
  "datasets": [
    {
      "name": "squad_v2",
      "author": "stanford",
      "description": "Stanford Question Answering Dataset v2.0",
      "size": {
        "train": 130319,
        "validation": 11873,
        "total": 142192
      },
      "license": "cc-by-sa-4.0",
      "languages": ["en"],
      "tasks": ["question-answering", "extractive-qa"],
      "downloads": 1234567,
      "likes": 5678,
      "url": "https://huggingface.co/datasets/squad_v2",
      "last_modified": "2024-01-15T10:30:00Z"
    }
  ],
  "total_results": 42,
  "query": "question answering english"
}
```

## HuggingFace Hub API Integration

Use the HuggingFace Hub API:

```python
from huggingface_hub import HfApi, list_datasets

api = HfApi()

def search_datasets(query: str, **filters) -> list:
    datasets = list_datasets(
        search=query,
        filter=filters.get('task'),
        language=filters.get('language'),
        limit=filters.get('limit', 10),
        sort='downloads',
        direction=-1  # Descending
    )

    results = []
    for ds in datasets:
        # Filter by license if specified
        if filters.get('license') and not matches_license(ds.license, filters['license']):
            continue

        results.append({
            'name': ds.id,
            'author': ds.author,
            'description': ds.description,
            'license': ds.license,
            'downloads': ds.downloads,
            'likes': ds.likes,
            'tags': ds.tags,
            'url': f"https://huggingface.co/datasets/{ds.id}"
        })

    return results
```

## License Mapping

| Filter Value | Included Licenses |
|--------------|-------------------|
| `permissive` | MIT, Apache-2.0, BSD-*, CC-BY, CC0, Unlicense |
| `copyleft` | GPL-*, LGPL-*, AGPL-*, CC-BY-SA |
| `research-only` | Research-only, Non-commercial, Academic |
| `commercial` | MIT, Apache-2.0, BSD-*, CC0 |

## Task Mapping (HuggingFace Tasks)

| Soofi Task | HuggingFace Task Tags |
|------------|----------------------|
| `question-answering` | question-answering, extractive-qa, open-domain-qa |
| `summarization` | summarization, text2text-generation |
| `classification` | text-classification, sentiment-analysis |
| `ner` | token-classification, named-entity-recognition |
| `text-generation` | text-generation, language-modeling |
| `translation` | translation, machine-translation |

## MCP Tool Definition

```json
{
  "name": "search_huggingface_datasets",
  "description": "Search for datasets on HuggingFace Hub based on query and filters",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query for datasets"
      },
      "domain": {
        "type": "string",
        "description": "Domain filter (medical, legal, code, finance)"
      },
      "task": {
        "type": "string",
        "description": "Task filter (question-answering, summarization, classification, ner)"
      },
      "language": {
        "type": "string",
        "description": "Language filter (de, en, multi)"
      },
      "license": {
        "type": "string",
        "description": "License filter (permissive, copyleft, research-only, commercial)"
      },
      "min_size": {
        "type": "integer",
        "description": "Minimum dataset size"
      },
      "limit": {
        "type": "integer",
        "description": "Maximum number of results",
        "default": 10
      }
    },
    "required": ["query"]
  }
}
```

## Implementation Options

### Option A: Separate MCP Server
Create a separate MCP server for HuggingFace:
- `huggingface-mcp-server/`
- Dockerfile for containerization
- Integration in docker-compose.yml

### Option B: Extension of Existing Agent
Integrate HuggingFace search directly into the LangGraph agent as a tool:
- `agent/tools/huggingface_search.py`
- Less infrastructure, but less modular

### Recommendation: Option A
For better separation of concerns and reusability.

# Acceptance Criteria

- [ ] MCP server endpoint implemented
- [ ] Search by query works
- [ ] Filter by task, language, license works
- [ ] Response contains all relevant fields
- [ ] Results are sorted by downloads
- [ ] Rate limiting for HuggingFace API respected
- [ ] Docker container for the server

# Branches

- feature/US-05-huggingface-search
