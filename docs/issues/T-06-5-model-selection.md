# Task

- user story: [US-06](US-06-inference-server.md)

# Description

**Model Evaluation & Deployment on Triton**

Evaluate, download, and deploy suitable models on the Triton inference server (H200 GPU). This covers both the chat model and the embedding model for the Soofi Trainer demo.

Repository: [soofi-inference-server](https://mrk40.dfki.de/soofi/soofi-inference-server)

## Chat Model

Evaluate models for the conversational agent. Requirements:
- German language capability (agent speaks German)
- Instruction-following / chat format
- Fits on a single H200 (80 GB VRAM)
- Served via vLLM with OpenAI-compatible API

Candidates to evaluate:
| Model | Size | Quantization | Notes |
|-------|------|-------------|-------|
| `mistralai/Mistral-7B-Instruct-v0.3` | 7B | AWQ | Lightweight, good baseline |
| `mistralai/Mixtral-8x7B-Instruct-v0.1` | 8x7B | AWQ | MoE, strong multilingual |
| `meta-llama/Llama-3.1-8B-Instruct` | 8B | AWQ | Strong instruction following |
| `Qwen/Qwen2.5-7B-Instruct` | 7B | AWQ | Excellent multilingual |

## Embedding Model

Evaluate embedding models for semantic search over the German knowledge base. Requirements:
- **Multilingual support is critical** — the knowledge base is in German
- Good retrieval quality for German technical text
- Servable via Triton or accessible as OpenAI-compatible endpoint

Candidates to evaluate:
| Model | Dimensions | Multilingual | Notes |
|-------|-----------|-------------|-------|
| `intfloat/multilingual-e5-large` | 1024 | Yes | Strong multilingual retrieval |
| `BAAI/bge-m3` | 1024 | Yes | Multi-granularity, 100+ languages |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384 | Yes | Lightweight, good German support |
| `jinaai/jina-embeddings-v3` | 1024 | Yes | State-of-the-art multilingual |

## Deployment Steps

1. **Select models**: Run benchmarks / qualitative tests to pick one chat and one embedding model
2. **Download**: Use the existing `download-model.sh` script in soofi-inference-server
3. **Configure**: Create or update `config.pbtxt` for each model in the Triton model repository
4. **Verify**: Confirm models load on the H200 and respond correctly via the OpenAI-compatible API
5. **Document**: Record chosen models, VRAM usage, and any quantization details

## Acceptance Criteria

- [ ] Chat model selected and deployed on Triton (serves German conversation)
- [ ] Embedding model selected and deployed on Triton (multilingual, works with German text)
- [ ] Models downloaded via `download-model.sh`
- [ ] `config.pbtxt` configured for each model
- [ ] Models verified working via OpenAI-compatible API endpoint
- [ ] Model choices and rationale documented

# Branches
