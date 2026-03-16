# Task

- user story: [US-01](US-01-infrastructure.md)

/label ~UserStory_US-01
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Environment Configuration Cleanup**

Clean up environment variable handling across the stack for consistency and clarity. Internal variables should not be exposed in `.env` or documented in the README.

## Changes

### Remove internal variables from `.env`
- `WEAVIATE_GRPC_PORT` — internal port, not user-configurable
- Hardcode these values directly in `docker-compose.yml`

### Remove docker-compose fallback defaults
- Remove `:-` fallback defaults from `docker-compose.yml` (e.g. `${WEAVIATE_PORT:-8070}`)
- `.env` is the single source of truth — if a variable is missing, it should fail loudly rather than fall back silently

### README updates
- Remove internal variables from the Configuration table (e.g. `WEAVIATE_GRPC_PORT`)
- Ensure documented defaults match `.env` values

## Acceptance Criteria

- [ ] No internal-only variables in `.env`
- [ ] No `:-` fallback defaults in `docker-compose.yml`
- [ ] README Configuration table only lists user-facing variables
- [ ] README defaults match `.env` values
- [ ] Stack starts correctly with `./up.sh`
