# Task

- user story: #US-03

/label ~UserStory_US-03
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Structured Recommendation Report**

The agent generates a structured output with a primary recommendation, alternatives, and next steps.

## Report Structure

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

## Output Format

The report is output as well-formatted Markdown in the chat. It should be readable and actionable.

## Acceptance Criteria

- [ ] Report contains primary recommendation with reasoning
- [ ] Estimated resources (hardware, time, cost) are included
- [ ] 1–2 alternatives are listed with trade-offs
- [ ] Next steps are concrete and actionable
- [ ] Report is well-formatted and readable
- [ ] Dataset recommendation is included when a HuggingFace search was performed

# Branches

- feature/US-03-agent-architecture
