# Task

- user story: #US-03

/label ~UserStory_US-03
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**CI Pipeline for Unit Tests**

Set up a CI pipeline that runs unit tests for the agent's decision logic and other testable components.

## Scope

- Run unit tests for the decision logic (T-03-3)
- Run linting for agent code (e.g. ruff, black)
- Pipeline triggers on push and merge requests

## Requirements

- Pipeline runs against the agent code
- Tests are executed automatically
- Linting ensures code quality and consistent formatting
- Pipeline fails clearly on test failures or lint errors

## Acceptance Criteria

- [ ] CI pipeline is configured and runs on push/MR
- [ ] Unit tests for decision logic are executed
- [ ] Linting runs against agent code
- [ ] Pipeline reports pass/fail clearly

# Branches

- feature/US-03-agent-architecture
