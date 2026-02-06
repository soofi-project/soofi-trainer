# Task

- user story: #US-01

/label ~UserStory_US-01
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**GitLab CI/CD Pipeline**

Set up GitLab CI for automated builds and tests.

## Pipeline Stages

| Stage | Description |
|-------|-------------|
| Lint | Python linting (ruff, black) and YAML validation |
| Test | Unit tests (pytest) and Docker Compose config validation |
| Build | Build Docker images for custom services (agent) |
| Deploy | (Optional) Push images to registry and deploy to staging |

## Requirements

- Pipeline runs on push and merge requests
- Python code is linted and formatted
- Unit tests pass before build
- Docker Compose configuration is valid
- Docker images are built and tagged with commit SHA

## Acceptance Criteria

- [ ] `.gitlab-ci.yml` is in place
- [ ] Lint stage checks Python formatting and YAML validity
- [ ] Test stage runs unit tests
- [ ] Build stage creates Docker images
- [ ] Pipeline runs on push and merge requests

# Branches

- feature/US-01-infrastructure
