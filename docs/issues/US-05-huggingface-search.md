# User Story

- tasks:
  - #T-05-1
  - #T-05-2

/label ~UserStory
/milestone %ProductBacklog

# Story

*"As a user, I want the agent to find suitable datasets on HuggingFace, so that I know which data is available for my training."*

# Description

When the user has no own data or is looking for additional public datasets, the agent should be able to automatically search for suitable datasets on HuggingFace.

## Use Cases

1. **No own data**: User wants to do fine-tuning but has no training data
2. **Data augmentation**: User has own data but wants to augment with public datasets
3. **Benchmark search**: User is looking for evaluation datasets for their model
4. **Domain exploration**: User wants to know which datasets are available in their domain

## Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agent     │────▶│ HuggingFace │────▶│   Dataset   │
│             │     │ MCP Server  │     │   Results   │
│             │◀────│             │◀────│             │
└─────────────┘     └─────────────┘     └─────────────┘
```

1. Agent determines during interview: User needs datasets
2. Agent calls `search_huggingface_datasets` tool
3. MCP server searches HuggingFace Hub API
4. Agent presents top results with explanation
5. Agent recommends suitable dataset based on use case

## Search Criteria

The agent can filter by the following criteria:
- **Domain**: medical, legal, code, finance, etc.
- **Task**: question-answering, summarization, classification, ner, etc.
- **Language**: de, en, multi, etc.
- **License**: permissive (MIT, Apache), copyleft (GPL), research-only, etc.
- **Size**: Minimum/Maximum number of samples

## Result Presentation

The agent presents found datasets with:
- Dataset name and link
- Short description
- Size (number of samples)
- License
- Quality indicator (downloads, likes)
- Explanation why this dataset fits

# Acceptance Criteria

- [ ] HuggingFace MCP endpoint implemented (T-05-1)
- [ ] Agent can trigger dataset search
- [ ] Search results are filtered meaningfully
- [ ] Agent explains why datasets fit
- [ ] Dataset recommendation included in report (T-03-3)
