# Task

- user story: #US-01

/label ~UserStory_US-01
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Create Docker-Compose Foundation**

Create the Docker-Compose configuration for the Soofi Trainer stack.

## Reference Implementation

Use the existing setup from:
https://gitlab.basys.dfki.dev/hackathon/aas-document-rag/-/blob/master/docker-compose.yml

Extract and adapt these services:
- `weaviate` (lines 400-429)
- `aas-weaviate-mcp` (lines 344-360)
- `mcp-inspector` (lines 363-370)

## Services to Include

```yaml
services:
  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8070:8080"
      - "50051:50051"
    # ... (see reference)

  vector-mcp:
    image: dfkibasys/aas-vector-mcp:latest
    ports:
      - "8113:8000"
    environment:
      - WEAVIATE_HOST=weaviate
      - WEAVIATE_PORT=8080
      - EMBEDDING_MODEL=openai:text-embedding-3-small
    # ... (see reference)

  mcp-inspector:
    image: ghcr.io/modelcontextprotocol/inspector:latest
    # ... (see reference)

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
```

## Files to Create

- `docker-compose.yml`
- `.env.example` (with OPENAI_API_KEY, EMBEDDING_MODEL, etc.)
- `.gitignore`

# Branches

- feature/US-01-infrastructure
