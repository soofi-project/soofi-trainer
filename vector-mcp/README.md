# AAS Vector MCP Server

MCP (Model Context Protocol) server for querying AAS documentation in vector databases with metadata filtering.

**Current Implementation:** Weaviate  
**Planned Support:** Qdrant, Pinecone, ChromaDB, Milvus

**Version:** 0.1.0

## Why MCP?

This MCP server solves a critical limitation when using Weaviate with AI agents in platforms like Flowise:

### The Problem
- **No native filtering in Flowise**: AI agents in Flowise cannot filter Weaviate queries by metadata (e.g., `submodel_id`, `idShortPath`)
- **Limited customization**: Implementing complex RAG patterns (reranking, chunk prefetching, context optimization) directly in Flowise TypeScript tools is cumbersome
- **Validation gaps**: No type-safe argument validation or proper error handling

### The MCP Solution
By exposing Weaviate as an MCP server, we gain:

1. **Metadata Filtering**: Required `submodel_id` and optional `idShortPath` filtering enforced at the tool level
2. **Type-Safe API**: Explicit function signatures with argument validation in Python
3. **Extensibility**: Easy to add advanced RAG patterns:
   - **Reranking**: Integrate reranking models to improve result relevance
   - **Chunk prefetching**: Fetch surrounding chunks for better context
   - **Agentic reranking**: Run a secondary AI model behind the MCP endpoint for intelligent result filtering
   - **Context window optimization**: Process and compress results before sending to main agent
4. **Interaction Examples**: MCP supports tool usage examples and additional documentation resources
5. **Consistent Embedding**: Uses the same embedding model as the ingestion pipeline via LangChain

### Architecture Benefits

```
┌─────────────┐         ┌──────────────────┐         ┌───────────┐
│  Flowise    │────────>│  MCP Server      │────────>│ Weaviate  │
│  (Agent)    │  HTTP   │  - Filtering     │  gRPC   │ (Vectors) │
│             │         │  - Validation    │         │           │
│             │         │  - Reranking     │         │           │
│             │         │  - Optimization  │         │           │
└─────────────┘         └──────────────────┘         └───────────┘
                               │
                               │ Embedding Model
                               │ (Same as ingest)
                               ▼
                        ┌──────────────┐
                        │  LangChain   │
                        │  Embeddings  │
                        └──────────────┘
```

**Key advantage**: The MCP server already has an embedding model loaded for query vectorization. This same model can be leveraged for reranking, semantic filtering, or even agentic processing—all without bloating the main agent's context window.

## Features

- **search_documents**: Semantic search with required `submodel_id` and optional `idShortPath` filtering
- **list_metadata_values**: Discover available metadata values
- **Multi-architecture support**: amd64, arm64
- **Configurable embedding models**: OpenAI, Google Gemini, Voyage AI, Ollama
- **Extensible architecture**: Ready for reranking, chunk prefetching, and agentic RAG patterns

## Installation

### From Source
```bash
git clone https://gitlab.basys.dfki.dev/hackathon/aas-vector-mcp.git
cd aas-vector-mcp
pip install -e .
```

## Usage

### Local (stdio transport)

```bash
export WEAVIATE_HOST=localhost
export WEAVIATE_PORT=8070
export EMBEDDING_MODEL=openai:text-embedding-3-small
export OPENAI_API_KEY=sk-...
python -m aas_weaviate_mcp.server
```

### Docker

#### Pull from Docker Hub

```bash
docker pull dfkibasys/aas-vector-mcp:0.1.0
docker run -p 8000:8000 \
  -e WEAVIATE_HOST=weaviate \
  -e WEAVIATE_PORT=8080 \
  -e EMBEDDING_MODEL=openai:text-embedding-3-small \
  -e OPENAI_API_KEY=sk-... \
  dfkibasys/aas-vector-mcp:0.1.0
```

#### Build locally

```bash
docker build -t aas-vector-mcp:0.1.0 .
docker run -p 8000:8000 \
  -e WEAVIATE_HOST=weaviate \
  -e WEAVIATE_PORT=8080 \
  -e EMBEDDING_MODEL=openai:text-embedding-3-small \
  -e OPENAI_API_KEY=sk-... \
  aas-vector-mcp:0.1.0
```

### In docker-compose

```yaml
aas-vector-mcp:
  image: dfkibasys/aas-vector-mcp:0.1.0
  ports:
    - "8113:8000"
  environment:
    - WEAVIATE_HOST=weaviate
    - WEAVIATE_PORT=8080
    - EMBEDDING_MODEL=openai:text-embedding-3-small
    - OPENAI_API_KEY=${OPENAI_API_KEY}
  networks:
    - embedding
```

## MCP Client Configuration

### Claude Desktop / Cline

```json
{
  "mcpServers": {
    "aas-vector": {
      "url": "http://localhost:8113/mcp/",
      "transport": "http"
    }
  }
}
```

### Flowise

Add as Custom MCP Tool:
- URL: `http://localhost:8113/mcp/` (or `http://aas-vector-mcp:8000/mcp/` from within Docker)
- Transport: HTTP

## Tools

### search_documents

```python
search_documents(
    query="temperature specifications",
    submodel_id="http://aas.dfki.de/ids/sm/identification_mir100_01",
    idShortPath="Documentation",  # optional
    limit=5
)
```

Returns:
```json
{
  "results": [
    {
      "text": "Chunk content...",
      "metadata": {
        "submodel_id": "http://...",
        "idShortPath": "Documentation",
        "source": "/aasx/MiR100-User-guide.pdf"
      },
      "distance": 0.123
    }
  ],
  "total": 5,
  "query": "temperature specifications",
  "filters_applied": {
    "submodel_id": "http://...",
    "idShortPath": "Documentation"
  }
}
```

### list_metadata_values

```python
list_metadata_values(
    field="submodel_id",
    limit=20
)
```

## Environment Variables

### Weaviate Connection

| Variable | Description | Default |
|----------|-------------|---------|
| `WEAVIATE_SCHEME` | http or https | `http` |
| `WEAVIATE_HOST` | Weaviate host | `localhost` |
| `WEAVIATE_PORT` | Weaviate HTTP port | `8080` |
| `WEAVIATE_GRPC_PORT` | Weaviate gRPC port | `50051` |
| `WEAVIATE_COLLECTION` | Collection name | `Docs` |

### Embedding Model (required)

| Variable | Description | Example |
|----------|-------------|---------|
| `EMBEDDING_MODEL` | Model in `provider:model` format | `openai:text-embedding-3-small` |

**Supported providers via LangChain:**
- `openai` - OpenAI embedding models
- `google_genai` - Google Gemini embedding models  
- `voyageai` - Voyage AI (Anthropic-recommended)
- `ollama` - Local Ollama models (nomic-embed-text, mxbai-embed-large, etc.)

### API Keys (depending on provider)

| Variable | Provider | Required |
|----------|----------|----------|
| `OPENAI_API_KEY` | OpenAI | Yes for `openai:*` |
| `GOOGLE_API_KEY` | Google/Gemini | Yes for `google_genai:*` |
| `VOYAGE_API_KEY` | Voyage AI | Yes for `voyageai:*` |
| `OLLAMA_HOST` | Ollama (local) | No key needed, default: `http://localhost:11434` |

### Example Configurations

**OpenAI (cloud):**
```bash
EMBEDDING_MODEL=openai:text-embedding-3-small
OPENAI_API_KEY=sk-...
```

**Voyage AI (Anthropic-recommended):**
```bash
EMBEDDING_MODEL=voyageai:voyage-3
VOYAGE_API_KEY=pa-...
```

**Ollama (local, no API costs):**
```bash
EMBEDDING_MODEL=ollama:nomic-embed-text
OLLAMA_HOST=http://localhost:11434
```

**Google Gemini:**
```bash
EMBEDDING_MODEL=google_genai:text-embedding-004
GOOGLE_API_KEY=...
```

---

## Multi-Architecture Docker Deployment

### Prerequisites

You need Docker BuildKit with buildx and QEMU for multi-platform builds:

```bash
# Verify buildx is available
docker buildx version

# Create and use a new builder instance (one-time setup)
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap

# Verify QEMU is available for cross-platform emulation
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

### Build and Push to Docker Hub

#### 1. Login to Docker Hub

```bash
docker login
```

#### 2. Build for Multiple Architectures

```bash
# Build and push for amd64 and arm64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t dfkibasys/aas-vector-mcp:0.1.0 \
  -t dfkibasys/aas-vector-mcp:latest \
  --push \
  .
```

This will:
- Build images for both `linux/amd64` (Intel/AMD) and `linux/arm64` (ARM, e.g., Apple Silicon, Raspberry Pi)
- Tag with version `0.1.0` and `latest`
- Push directly to Docker Hub

#### 3. Verify Multi-Arch Images

```bash
docker buildx imagetools inspect dfkibasys/aas-vector-mcp:0.1.0
```

You should see both `linux/amd64` and `linux/arm64` in the output.

### Build Without Pushing (local testing)

```bash
# Load image for your current platform
docker buildx build \
  --platform linux/amd64 \
  -t aas-vector-mcp:0.1.0-local \
  --load \
  .

# Test locally
docker run -p 8000:8000 aas-vector-mcp:0.1.0-local
```

### Notes on Multi-Arch Builds

- **Build time**: Cross-platform builds using QEMU are significantly slower than native builds (especially arm64 on amd64 host)
- **Cache**: Buildx maintains separate caches per platform
- **Testing**: For thorough testing, run on actual hardware of each architecture when possible
- **CI/CD**: GitHub Actions and GitLab CI support multi-arch builds natively via buildx

---

## Development

### Running Tests

```bash
# TODO: Add pytest configuration
pytest
```

### Code Style

```bash
# Format code
black src/

# Lint
ruff check src/
```

## Architecture

### Lokale Embedding-Optionen

Für souveräne KI-Deployments ohne externe API-Abhängigkeiten:

**Ollama** (empfohlen für lokales Setup):
- Models: `nomic-embed-text`, `mxbai-embed-large`
- Docker-ready, einfach zu integrieren
- Keine API-Keys erforderlich

## Roadmap

### Multi-Vector-Database Support
Planned: Qdrant, Pinecone, ChromaDB, Milvus via pluggable backend architecture.

### Advanced RAG Features
- Reranking, chunk prefetching, agentic processing
- Hybrid search, query expansion
- MCP tool usage examples and documentation resources

## License

MIT