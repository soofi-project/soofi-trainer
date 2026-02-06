# Task

- user story: #US-01

/label ~UserStory_US-01
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**n8n Setup with Dummy Chatbot**

Set up n8n as the agent backend and create a simple chatbot workflow. Open WebUI connects to n8n so that user messages are processed by n8n and a response is returned. This serves as an initial integration test for the end-to-end connection.

## n8n Setup

- n8n runs as a container in the Docker stack
- Persistent data volume so local workflow changes are never lost (even without export)
- Accessible via browser for workflow editing

## Workflow Management

- Shared workflows are stored as JSON files in the repo (e.g. `n8n/workflows/`)
- Persistent data volume keeps the local state safe during normal usage
- On fresh start (after `down.sh --clean` or first setup), workflows from the repo are automatically imported into n8n
- To share workflow changes with the team: export from n8n, commit the JSON to the repo
- Depends on T-01-2 (Stack Management Scripts) for the `--clean` flag behavior

## Dummy Chatbot Workflow

- n8n exposes an endpoint that Open WebUI can call
- The workflow receives a user message and returns a simple response
- This is a minimal proof-of-concept — the actual agent logic (LangGraph, RAG) comes later

## Open WebUI Connection

- Open WebUI is configured to use n8n as its backend
- User messages entered in Open WebUI are sent to n8n
- n8n's response is displayed in the Open WebUI chat

## Acceptance Criteria

- [ ] n8n is running as part of the Docker stack
- [ ] n8n is accessible via browser for workflow editing
- [ ] A simple chatbot workflow exists in n8n
- [ ] Open WebUI is connected to n8n as backend
- [ ] End-to-end interaction works: question in Open WebUI → response from n8n
- [ ] Workflows persist across container restarts (persistent volume)
- [ ] Shared workflows are stored as JSON in the repo
- [ ] After `down.sh --clean` + `up.sh`, workflows are imported from the repo
- [ ] Verify that n8n supports importing workflows into an empty database on startup

# Branches

- feature/US-01-infrastructure
