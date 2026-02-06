# Task

- user story: #US-03

/label ~UserStory_US-03
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Decision Logic for Method Selection**

Implement a decision tree and multi-criteria evaluation for selecting the optimal LLM specialization method based on the user's situation.

## Decision Tree

The agent uses a decision tree as a first pass to narrow down suitable methods:

| Condition | Recommendation |
|-----------|---------------|
| Large amount of unlabeled domain data | Continued Pretraining or SFT |
| Labeled data + sufficient GPU resources | Full Fine-Tuning (SFT) |
| Labeled data + limited GPU resources | LoRA / QLoRA |
| No own data + public datasets available | Search HuggingFace → then PEFT |
| Factual knowledge more important than parameterization | RAG (+ optional light fine-tuning) |
| Alignment / preferences important | DPO or RLHF (depending on budget) |
| Deployment constraints dominate | Knowledge Distillation |

## Multi-Criteria Evaluation

For each candidate method, a score is calculated based on weighted criteria:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Data Availability | 0.25 | How well do the available data fit the method? |
| Budget Match | 0.20 | Does the budget match the method's requirements? |
| Task Suitability | 0.25 | How well suited is the method for the task? |
| Expertise Requirement | 0.15 | Does the required expertise match the team? |
| Success Probability | 0.15 | How likely is success given the constraints? |

## Output

The agent outputs the **top 3 recommendations** with:
- Method name and total score
- Reasoning per criterion
- Specific hints for the user's use case

## Acceptance Criteria

- [ ] Decision tree narrows down suitable methods
- [ ] Multi-criteria evaluation scores candidate methods
- [ ] Agent outputs top 3 recommendations with reasoning
- [ ] Reasoning is comprehensible and use-case-specific
- [ ] Unit tests cover decision logic

# Branches

- feature/US-03-agent-architecture
