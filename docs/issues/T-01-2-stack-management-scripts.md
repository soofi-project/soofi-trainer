# Task

- user story: [US-01](US-01-infrastructure.md)

/label ~UserStory_US-01
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Stack Management Scripts**

Create convenience scripts for stack management.

## up.sh

- Check if `.env` exists, copy from `.env.example` if not
- Check if the secrets file referenced by `ENV_SECRETS_FILE` exists and warn if missing
- Start all containers
- Wait for services to be healthy
- Display all service URLs when ready

## down.sh

- Stop all containers
- Option `--clean` to also delete volumes
- Confirmation message

## Acceptance Criteria

- [ ] `./up.sh` starts the full stack and displays service URLs
- [ ] `./up.sh` warns if the secrets file (`ENV_SECRETS_FILE`) is missing
- [ ] `./down.sh` stops all containers
- [ ] `./down.sh --clean` removes volumes as well
- [ ] Missing `.env` is handled gracefully

# Branches

- feature/US-01-infrastructure
