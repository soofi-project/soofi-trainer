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

```yaml
stages:
  - lint
  - test
  - build
  - deploy
```

## Jobs

### Lint
- Python: ruff, black --check
- YAML: yamllint for docker-compose

### Test
- Python unit tests (pytest)
- Docker compose config validation

### Build
- Build Docker images for custom services (agent)
- Tag with commit SHA and version

### Deploy (optional)
- Push images to registry
- Deploy to staging environment

## .gitlab-ci.yml

```yaml
image: python:3.11-slim

stages:
  - lint
  - test
  - build

variables:
  DOCKER_DRIVER: overlay2

lint:python:
  stage: lint
  script:
    - pip install ruff black
    - ruff check agent/
    - black --check agent/

lint:yaml:
  stage: lint
  image: cytopia/yamllint
  script:
    - yamllint docker-compose.yml

test:unit:
  stage: test
  script:
    - pip install -r agent/requirements.txt
    - pip install pytest
    - pytest agent/tests/ -v

test:compose:
  stage: test
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker compose config

build:agent:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t soofi-agent:$CI_COMMIT_SHA agent/
  only:
    - main
    - merge_requests
```

## Registry

Push images to GitLab Container Registry:
- `registry.basys.dfki.dev/soofi/soofi-trainer/agent:latest`

# Branches

- feature/US-01-infrastructure
