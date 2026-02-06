# Task

- user story: #US-01

/label ~UserStory_US-01
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Stack Management Scripts**

Create convenience scripts for stack management.

## up.sh

- Check if `.env` exists, copy from `.env.example` if not
- Warn if `OPENAI_API_KEY` is not set
- Start all containers
- Wait for services to be healthy
- Display all service URLs when ready

## down.sh

- Stop all containers
- Option `--clean` to also delete volumes
- Confirmation message

## Acceptance Criteria

- [ ] `./up.sh` starts the full stack and displays service URLs
- [ ] `./down.sh` stops all containers
- [ ] `./down.sh --clean` removes volumes as well
- [ ] Missing `.env` is handled gracefully

# Branches

- feature/US-01-infrastructure
