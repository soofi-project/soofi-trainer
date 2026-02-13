# Task

- user story: #5

/label ~UserStory_US-02
/label ~Task
/label ~ToDo

# Description

**MinIO for Knowledge Source URLs**

Add a MinIO (S3-compatible) container to the stack so that knowledge documents are accessible via HTTP URLs. The ingestion container uploads each markdown file to MinIO and stores the resulting URL as `source` in Weaviate. This allows the agent to cite clickable source links in its responses.

## Motivation

Currently `source` stores a relative file path (e.g. `methods/lora.md`) which is not useful for end users. For demos (e.g. Hannover Messe) and production use, the agent should show clickable links that open the original document. MinIO provides neutral, self-hosted URLs without exposing internal infrastructure like GitLab.

## Architecture

```
knowledge/ (volume) --> knowledge-ingestion --> MinIO (upload .md)
                                            --> Weaviate (store MinIO URL as source)

Agent response: "Quelle: [LoRA](https://demo.soofi.dfki.de/knowledge/methods/lora.md)"
```

## Source URL via Meta Files

The source URL is defined in each `-meta.yaml` file with environment variable substitution:

```yaml
# lora-meta.yaml
topic: fine_tuning
category: method
source: ${KNOWLEDGE_BASE_URL}/methods/lora.md
```

The ingestion container resolves `${...}` placeholders at runtime. The base URL is configured per environment:

| Environment | KNOWLEDGE_BASE_URL |
|---|---|
| Local dev | `http://localhost:9000/knowledge` |
| Demo | `https://demo.soofi.dfki.de/knowledge` |
| Production | `https://knowledge.soofi.io` |

If no `source` field is present in the YAML, the ingestion falls back to the relative file path (backwards compatible).

## Implementation

- Add MinIO as a new service in `docker-compose.yml`
- Ingestion container uploads each `.md` file to a MinIO bucket
- Ingestion container resolves `${ENV_VAR}` placeholders in the `source` meta field
- Store the resolved URL as `source` in Weaviate
- MinIO bucket should be publicly readable (no auth needed for GET)
- Configure via env vars: `KNOWLEDGE_BASE_URL`, `MINIO_ENDPOINT`, `MINIO_BUCKET`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`

## Acceptance Criteria

- [ ] MinIO service runs in docker-compose
- [ ] Knowledge markdown files are uploaded to MinIO bucket
- [ ] MinIO bucket is publicly readable
- [ ] `source` field in Weaviate contains resolved HTTP URLs
- [ ] `${ENV_VAR}` placeholders in `-meta.yaml` are resolved at runtime
- [ ] Fallback to relative file path if no `source` in meta YAML
- [ ] Agent can cite clickable source links in responses

# Branches

- feature/T-02-4-minio-knowledge-urls
