# Task

- user story: #US-05

/label ~UserStory_US-05
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Agent Integration for HuggingFace Dataset Search**

Integrate the HuggingFace dataset search into the LangGraph agent.

## Trigger Conditions

The agent calls `search_huggingface_datasets` when:

1. **No own data**
   - User indicated in interview that they have no own data
   - Agent offers: "Soll ich nach passenden öffentlichen Datensätzen suchen?"

2. **Explicit request**
   - User explicitly asks for datasets
   - "Are there public datasets for [domain]?"

3. **Recommendation requires data**
   - Agent recommends fine-tuning method
   - But user has no data
   - → Automatic search for suitable datasets

## Agent Workflow

```python
class DatasetSearchNode:
    """LangGraph node for dataset search."""

    async def should_search(self, state: AgentState) -> bool:
        """Check if dataset search is needed."""
        return (
            not state.user_has_data and
            state.recommendation_requires_data and
            state.user_wants_dataset_search
        )

    async def search_datasets(self, state: AgentState) -> AgentState:
        """Execute dataset search."""
        query = self._build_query(state)
        filters = self._build_filters(state)

        results = await self.mcp_client.call(
            "search_huggingface_datasets",
            query=query,
            **filters
        )

        state.dataset_results = results
        return state

    def _build_query(self, state: AgentState) -> str:
        """Build search query from context."""
        parts = []
        if state.domain:
            parts.append(state.domain)
        if state.task:
            parts.append(state.task)
        if state.language:
            parts.append(state.language)
        return " ".join(parts)

    def _build_filters(self, state: AgentState) -> dict:
        """Build filters from context."""
        return {
            'task': state.task,
            'language': state.language,
            'license': state.license_preference,
            'limit': 5
        }
```

## Result Presentation

The agent presents found datasets in a user-friendly way:

```python
DATASET_PRESENTATION_TEMPLATE = """
Ich habe {count} passende Datensätze auf HuggingFace gefunden:

{dataset_list}

**Meine Empfehlung**: {top_recommendation}

{reasoning}
"""

DATASET_ITEM_TEMPLATE = """
### {number}. {name}
- **Beschreibung**: {description}
- **Größe**: {size:,} Samples
- **Lizenz**: {license}
- **Downloads**: {downloads:,}
- **Link**: [{name}]({url})
"""
```

## Recommendation Logic

The agent selects the best dataset based on:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Task Match | 0.30 | Does the dataset fit the task? |
| Size Match | 0.25 | Is the size appropriate for the method? |
| License | 0.20 | Does the license fit the requirements? |
| Quality | 0.15 | Downloads/likes as quality indicator |
| Recency | 0.10 | How recent is the dataset? |

```python
def rank_datasets(datasets: list, user_context: UserContext) -> list:
    """Rank datasets by suitability."""
    scored = []
    for ds in datasets:
        score = (
            task_match(ds, user_context.task) * 0.30 +
            size_match(ds, user_context.method) * 0.25 +
            license_match(ds, user_context.license_pref) * 0.20 +
            quality_score(ds) * 0.15 +
            recency_score(ds) * 0.10
        )
        scored.append((ds, score))

    return sorted(scored, key=lambda x: x[1], reverse=True)
```

## Integration in Recommendation Report

The found dataset is integrated into the recommendation report (T-03-5):

```markdown
### Recommended Dataset

Based on your use case, I recommend the dataset **{name}**:

- **Why this dataset fits**: {reasoning}
- **Size**: {size:,} samples (sufficient for {method})
- **License**: {license} ({license_implication})
- **Next step**: `datasets.load_dataset("{name}")`
```

## Error Handling

```python
async def handle_search_error(self, error: Exception, state: AgentState) -> str:
    """Handle errors during dataset search."""

    if isinstance(error, RateLimitError):
        return "Die HuggingFace-Suche ist gerade überlastet. Bitte versuche es in einigen Minuten erneut."

    if isinstance(error, NoResultsError):
        return f"Ich konnte leider keine Datensätze für '{state.query}' finden. Möchtest du die Suchkriterien anpassen?"

    return "Bei der Datensatz-Suche ist ein Fehler aufgetreten. Du kannst auch direkt auf huggingface.co/datasets suchen."
```

## State Extension

Extend `AgentState` with:

```python
@dataclass
class AgentState:
    # ... existing fields ...

    # Dataset Search
    user_wants_dataset_search: bool = False
    dataset_results: list[Dataset] = field(default_factory=list)
    recommended_dataset: Optional[Dataset] = None
    dataset_search_error: Optional[str] = None
```

# Acceptance Criteria

- [ ] Agent recognizes when dataset search is useful
- [ ] Agent calls HuggingFace MCP correctly
- [ ] Search results are presented in user-friendly way
- [ ] Agent provides recommendation with reasoning
- [ ] Dataset appears in recommendation report
- [ ] Error handling works

# Branches

- feature/US-05-huggingface-search
