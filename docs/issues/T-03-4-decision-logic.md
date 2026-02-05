# Task

- user story: #US-03

/label ~UserStory_US-03
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Decision Logic for Method Selection**

Implement the decision tree and multi-criteria evaluation for selecting the optimal specialization method.

## Decision Tree

```
IF own data available AND large amount unlabeled
  → Recommendation: Continued Pretraining or SFT

ELIF own labeled data AND sufficient GPU resources
  → Recommendation: Full Fine-Tuning (SFT)

ELIF own labeled data AND limited GPU resources
  → Recommendation: LoRA/QLoRA

ELIF no own data AND open datasets available
  → Search on HuggingFace → then PEFT

ELIF factual knowledge more important than parameterization
  → Recommendation: RAG + (optional light fine-tuning)

ELIF alignment/preferences important
  → Recommendation: DPO or RLHF (depending on budget)

ELIF deployment constraints dominate
  → Recommendation: Knowledge Distillation
```

## Multi-Criteria Evaluation

For each candidate method, a score is calculated based on:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Data Availability | 0-1 | How well do the available data fit the method? |
| Budget Match | 0-1 | Does the budget match the method's requirements? |
| Task Suitability | 0-1 | How well suited is the method for the task? |
| Expertise Requirement | 0-1 | Does the required expertise match the team? |
| Success Probability | 0-1 | How likely is success given the constraints? |

### Scoring Logic

```python
def calculate_method_score(method, user_context):
    scores = {
        'data_fit': evaluate_data_fit(method, user_context.data),
        'budget_match': evaluate_budget_match(method, user_context.budget),
        'task_suitability': evaluate_task_fit(method, user_context.task),
        'expertise_match': evaluate_expertise(method, user_context.expertise),
        'success_probability': estimate_success(method, user_context)
    }

    # Weighted average
    weights = {'data_fit': 0.25, 'budget_match': 0.20, 'task_suitability': 0.25,
               'expertise_match': 0.15, 'success_probability': 0.15}

    total_score = sum(scores[k] * weights[k] for k in scores)
    return total_score, scores
```

### Output

The agent outputs the **Top 3 recommendations** with:
- Method name
- Total score
- Reasoning per criterion
- Specific hints for the use case

## Implementation

Create `agent/decision_logic.py` with:
- `DecisionTree` class
- `MultiCriteriaEvaluator` class
- `MethodRecommender` class

## Method-Specific Scoring Rules

### Continued Pretraining
- `data_fit`: High with >100k unlabeled documents
- `budget_match`: High with >8 GPU-hours budget
- `task_suitability`: High for domain adaptation

### SFT (Supervised Fine-Tuning)
- `data_fit`: High with >1k labeled examples
- `budget_match`: Medium (4-8 GPU-hours)
- `task_suitability`: High for task-specific adaptation

### LoRA
- `data_fit`: Medium with >500 examples
- `budget_match`: High with limited VRAM (<24GB)
- `task_suitability`: High for fast iteration

### QLoRA
- `data_fit`: Medium with >500 examples
- `budget_match`: Very high for consumer GPUs (<16GB)
- `task_suitability`: High for large models (70B+)

### RAG
- `data_fit`: High for document corpora
- `budget_match`: Very high (no training)
- `task_suitability`: High for factual accuracy requirements

### DPO
- `data_fit`: High with preference pairs
- `budget_match`: Medium
- `task_suitability`: High for alignment requirements

### RLHF
- `data_fit`: Medium (needs human feedback)
- `budget_match`: Low (very expensive)
- `task_suitability`: Very high for safety requirements

### Knowledge Distillation
- `data_fit`: High with existing teacher model
- `budget_match`: Medium
- `task_suitability`: High for deployment constraints

# Acceptance Criteria

- [ ] Decision tree implemented
- [ ] Multi-criteria evaluation works
- [ ] Agent outputs top 3 recommendations
- [ ] Reasoning is comprehensible
- [ ] Unit tests for decision logic

# Branches

- feature/US-03-agent-architecture
