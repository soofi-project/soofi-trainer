# Task

- user story: #US-05

/label ~UserStory_US-05
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Agent Integration for HuggingFace Dataset Search**

Integrate the HuggingFace dataset search into the LangGraph agent so the agent can find suitable public datasets for the user.

## Trigger Conditions

The agent calls `search_huggingface_datasets` when:

1. **No own data** — User indicated in the interview that they have no training data
2. **Explicit request** — User explicitly asks for public datasets
3. **Recommendation requires data** — Agent recommends a fine-tuning method but the user has no data → automatic search

## Search Query Construction

The agent builds the search query from the interview context:
- Domain (e.g. medical, legal)
- Task (e.g. question-answering, classification)
- Language (e.g. German, English)
- License preferences

## Result Presentation

The agent presents found datasets in a user-friendly way:
- Dataset name and link
- Short description
- Size (number of samples)
- License
- Why this dataset fits the use case

## Dataset Ranking

The agent selects the best dataset based on weighted criteria:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Task Match | 0.30 | Does the dataset fit the user's task? |
| Size Match | 0.25 | Is the size appropriate for the recommended method? |
| License | 0.20 | Does the license fit the user's requirements? |
| Quality | 0.15 | Downloads/likes as quality indicator |
| Recency | 0.10 | How recent is the dataset? |

## Integration in Recommendation Report

The recommended dataset is included in the recommendation report (T-03-5) with:
- Why this dataset fits
- Size and suitability for the recommended method
- License implications
- How to get started with the dataset

## Error Handling

- **Rate limit exceeded** → Inform user, suggest trying again later
- **No results found** → Offer to adjust search criteria
- **API unavailable** → Suggest manual search on HuggingFace

## Acceptance Criteria

- [ ] Agent recognizes when dataset search is useful
- [ ] Agent calls HuggingFace MCP with appropriate query and filters
- [ ] Search results are presented in a user-friendly way
- [ ] Agent recommends a dataset with reasoning
- [ ] Dataset recommendation appears in the recommendation report
- [ ] Error cases are handled gracefully

# Branches

- feature/US-05-huggingface-search
