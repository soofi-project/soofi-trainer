# Task

- user story: #US-02

/label ~UserStory_US-02
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Knowledge Ingestion Container**

A Docker container that automatically creates the Weaviate collection and ingests all knowledge documents on `docker-compose up`. Uses file hashing for change detection so only modified files are re-ingested.

## Container Behavior

1. Wait for Weaviate to be healthy
2. Create collection `SoofiKnowledge` if it does not exist
3. Scan all `.md` files in the mounted `knowledge/` volume
4. For each file: compute SHA-256 hash
5. Compare hash against stored metadata in Weaviate
6. **New/changed files** → chunk, embed, and store with metadata
7. **Deleted files** (in Weaviate but no longer on disk) → remove entries
8. Log summary of changes and exit

## Collection Schema

| Property | Type | Description |
|----------|------|-------------|
| text | text | The chunk content |
| topic | text | Derived from folder name (e.g. `rag`, `fine_tuning`, `method`) |
| source | text | Relative file path (e.g. `rag/best_practices.md`) |
| source_hash | text | SHA-256 hash of the source file |
| category | text | Derived from file name (e.g. `best_practice`, `pitfall`, `use_case`, `method`) |

## Embedding

Use the same embedding model as configured in Vector MCP (default: `text-embedding-3-small`).

## Chunking Strategy

- Split by `##` headings (each H2 section becomes one chunk)
- If a section exceeds a reasonable size, split further by paragraphs
- Each chunk inherits metadata from the file path (folder → topic, filename → category)

## Change Detection

- Each file's SHA-256 hash is stored as `source_hash` in Weaviate
- On startup, the container compares the current file hash with the stored hash
- **Unchanged** → skip
- **New or changed** → delete old entries for that source, re-ingest
- **File deleted from disk** → remove all entries for that source from Weaviate

## Acceptance Criteria

- [ ] Container starts and completes on `docker-compose up`
- [ ] Collection `SoofiKnowledge` is created automatically
- [ ] All markdown files from `knowledge/` are ingested
- [ ] File hash is stored as metadata per entry
- [ ] Re-running the container skips unchanged files
- [ ] Modified files are re-ingested (old chunks deleted, new ones stored)
- [ ] Deleted files are cleaned up from Weaviate
- [ ] Ingestion summary is logged (added/updated/deleted/skipped counts)

# Branches

- feature/US-02-knowledge-base
