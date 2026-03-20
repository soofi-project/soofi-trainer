# User story

- tasks:
  - [T-04-1](T-04-1-huggingface-mcp.md) #14
  - [T-04-2](T-04-2-eclipse-dataspace-mcp.md) #15
  - [T-04-3](T-04-3-agent-integration.md) #16

# Story

*"As a user, I want the agent to find suitable datasets from multiple sources, so that I know which data is available for my training."*

# Description

When the user has no own data or is looking for additional public datasets, the agent should be able to automatically search for suitable datasets. The search is performed via separate MCP endpoints — one per data source — so that additional sources can be added in the future.

## Data Sources

| Source | MCP Endpoint | Task |
|--------|-------------|------|
| HuggingFace Hub | `search_huggingface_datasets` | [T-04-1](T-04-1-huggingface-mcp.md) |
| Eclipse Dataspace | `search_eclipse_dataspace` | [T-04-2](T-04-2-eclipse-dataspace-mcp.md) |

## Use Cases

1. **No own data**: User wants to do fine-tuning but has no training data
2. **Data augmentation**: User has own data but wants to augment with public datasets
3. **Benchmark search**: User is looking for evaluation datasets for their model
4. **Domain exploration**: User wants to know which datasets are available in their domain

## Workflow

```
                         +--------------+     +--------------+
                    +--->| HuggingFace  |---->|   Dataset    |
                    |    | MCP Server   |     |   Results    |
+--------------+    |    +--------------+     +--------------+
|   Agent      |----+
|              |    |    +--------------+     +--------------+
|              |    +--->|  Eclipse     |---->|   Dataset    |
+--------------+         | Dataspace   |     |   Results    |
                         | MCP Server  |     |              |
                         +--------------+     +--------------+
```

1. Agent determines during interview: User needs datasets
2. Agent calls one or both dataset search endpoints
3. MCP servers query their respective APIs
4. Agent presents combined top results with explanation
5. Agent recommends suitable dataset based on use case

## Search Criteria

The agent can filter by the following criteria (where supported by the source):
- **Domain**: medical, legal, code, finance, etc.
- **Task**: question-answering, summarization, classification, ner, etc.
- **Language**: de, en, multi, etc.
- **License**: permissive (MIT, Apache), copyleft (GPL), research-only, etc.
- **Size**: Minimum/Maximum number of samples

## Result Presentation

The agent presents found datasets with:
- Dataset name, source, and link
- Short description
- Size (number of samples)
- License
- Quality indicator (downloads, likes — where available)
- Explanation why this dataset fits

# Acceptance Criteria

- [ ] HuggingFace MCP endpoint implemented ([T-04-1](T-04-1-huggingface-mcp.md))
- [ ] Eclipse Dataspace MCP endpoint implemented ([T-04-2](T-04-2-eclipse-dataspace-mcp.md))
- [ ] Agent can trigger dataset search on one or both sources ([T-04-3](T-04-3-agent-integration.md))
- [ ] Search results are filtered meaningfully
- [ ] Agent explains why datasets fit
- [ ] Dataset recommendation included in report (#11)
