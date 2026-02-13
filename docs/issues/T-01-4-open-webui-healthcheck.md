# Task

- user story: #1

/label ~UserStory_US-01
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Override Open WebUI Healthcheck**

The Open WebUI Docker image defines a `HEALTHCHECK` without `--interval`, `--retries` or `--start-period`:

```dockerfile
HEALTHCHECK CMD curl --silent --fail http://localhost:${PORT:-8080}/health | jq -ne 'input.status == true' || exit 1
```

Docker falls back to defaults (30s interval, 3 retries, 0s start-period). With ~90s startup time, the container gets temporarily marked as "unhealthy" before it is ready.

## Solution

Override the healthcheck in `docker-compose.yml` with appropriate values, e.g.:

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl --silent --fail http://localhost:8080/health | jq -ne 'input.status == true' || exit 1"]
  interval: 15s
  timeout: 5s
  retries: 5
  start_period: 60s
```

## Acceptance Criteria

- [ ] Open WebUI healthcheck overridden in `docker-compose.yml` with `start_period`
- [ ] Container is not falsely marked as "unhealthy" during startup

# Branches


