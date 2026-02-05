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
- Start all containers with `docker compose up -d`
- Wait for services to be healthy
- Display all service URLs

## down.sh

- Stop all containers with `docker compose down`
- Option `--clean` to delete volumes
- Confirmation message

## Example Output

```
========================================
  Soofi Trainer - Starting Stack
========================================

[INFO] Starting containers...
[INFO] Waiting for services...

========================================
  Services are ready!
========================================

  Open WebUI:      http://localhost:3000
  Weaviate:        http://localhost:8070
  Vector MCP:      http://localhost:8113
  MCP Inspector:   http://localhost:5173

========================================
```

# Branches

- feature/US-01-infrastructure
