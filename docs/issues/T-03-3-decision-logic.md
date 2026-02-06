# Task

- user story: #US-03

/label ~UserStory_US-03
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Decision Logic & Recommendation Report**

Implement the decision tree and multi-criteria evaluation for selecting the optimal LLM specialization method, and generate a structured recommendation report.

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

## Recommendation Report

The agent generates a structured output with:

### 1. Primary Recommendation
- **Method name** and why it is optimal for the use case
- **Estimated resources**: hardware, training time, approximate cost
- **Recommended dataset** (if HuggingFace search was performed)

### 2. Alternatives
- 1–2 alternative methods
- When each alternative would be more suitable (e.g. if constraints change)
- Trade-offs compared to the primary recommendation

### 3. Next Steps
- **Prepare data**: specific instructions for data format and quality
- **Set up infrastructure**: hardware and software recommendations
- **Start training**: recommended approach and monitoring tips
- **Evaluation**: relevant metrics and benchmark recommendations

The report is output as well-formatted Markdown in the chat.

## Acceptance Criteria

- [ ] Decision tree narrows down suitable methods
- [ ] Multi-criteria evaluation scores candidate methods
- [ ] Agent outputs top 3 recommendations with reasoning
- [ ] Reasoning is comprehensible and use-case-specific
- [ ] Report contains primary recommendation with reasoning
- [ ] Estimated resources (hardware, time, cost) are included
- [ ] 1–2 alternatives are listed with trade-offs
- [ ] Next steps are concrete and actionable
- [ ] Dataset recommendation is included when a HuggingFace search was performed
- [ ] Unit tests cover decision logic

# Branches

- feature/US-03-agent-architecture
