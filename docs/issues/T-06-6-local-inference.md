# Task

- user story: [US-06](US-06-inference-server.md)

# Description

**Local Inference with Ollama / LM Studio**

Select suitable models for local development on PCs with 8 GB VRAM and document the setup for Ollama and LM Studio.

## Chat Model Selection

Requirements:
- German + English capability
- Fits in 8 GB VRAM (Q4 quantization)
- Available in both Ollama and LM Studio

Candidates to evaluate:
| Model | Quantization | VRAM (approx.) | Notes |
|-------|-------------|----------------|-------|
| `qwen2.5:7b` | Q4_K_M | ~5 GB | Excellent multilingual |
| `mistral:7b` | Q4_K_M | ~5 GB | Good all-rounder |
| `llama3.1:8b` | Q4_K_M | ~5 GB | Strong instruction following |
| `gemma2:9b` | Q4_K_M | ~6 GB | Good German quality |

## Embedding Model Selection

Requirements:
- **Multilingual** (German knowledge base)
- Lightweight enough for 8 GB GPU
- Available in Ollama

Candidates:
| Model | Dimensions | VRAM (approx.) | Notes |
|-------|-----------|----------------|-------|
| `nomic-embed-text` | 768 | ~270 MB | Already supported via `ollama:` provider |
| `mxbai-embed-large` | 1024 | ~670 MB | Good retrieval quality |
| `snowflake-arctic-embed` | 1024 | ~670 MB | Strong multilingual |

## Integration Steps

1. **Test models**: Run selected chat + embedding models locally, verify German quality
2. **Document Ollama setup**: `ollama pull`, verify API at `localhost:11434/v1`
3. **Document LM Studio setup**: Model download, enable local server, API endpoint
4. **`.env` examples**: Provide copy-paste config for both tools
5. **Docker integration**: Verify `host.docker.internal` works from containers to host Ollama/LM Studio
6. **README section**: Add "Local Inference" section with setup instructions for both tools

## `.env` Configuration

```bash
# Ollama (default port 11434)
CHAT_MODEL=qwen2.5:7b
OPENAI_API_BASE=http://host.docker.internal:11434/v1
EMBEDDING_MODEL=ollama:nomic-embed-text

# LM Studio (default port 1234)
CHAT_MODEL=qwen2.5-7b-instruct
OPENAI_API_BASE=http://host.docker.internal:1234/v1
EMBEDDING_MODEL=ollama:nomic-embed-text
```

## Acceptance Criteria

- [ ] Chat model selected and tested locally (German + English)
- [ ] Embedding model selected and tested locally (multilingual)
- [ ] Ollama setup documented in README
- [ ] LM Studio setup documented in README
- [ ] `.env` examples for both tools provided
- [ ] End-to-end test: agent conversation + knowledge search working with local models

# Branches
