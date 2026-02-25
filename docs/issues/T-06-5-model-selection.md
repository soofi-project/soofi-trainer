# Task

- user story: [US-06](US-06-inference-server.md)

# Description

**Model Evaluation & Deployment on Triton**

Evaluate and deploy suitable models on the Triton inference server (2x H200 NVL, 282 GB VRAM total).
This covers both the chat model and the embedding model for the Soofi Trainer.

Repository: [soofi-inference-server](https://mrk40.dfki.de/soofi/soofi-inference-server)

## Chat Model

Qwen 2.5 72B Instruct is currently deployed and running on both H200 GPUs via pipeline parallelism.
This task should evaluate whether the model meets the quality requirements for the Soofi Trainer
agent (German language, instruction following, tool use). If not, alternative models can be deployed
by editing `vars.yaml` — Ansible handles download and configuration automatically.

**Current deployment:**

| Model | Size | GPUs | Parallelism | Status |
|-------|------|------|-------------|--------|
| `Qwen/Qwen2.5-72B-Instruct` | 72B | 2x H200 | pipeline (pp=2) | deployed |

**Alternative candidates** (if Qwen 72B does not meet requirements):

| Model | Size | Notes |
|-------|------|-------|
| `meta-llama/Llama-3.3-70B-Instruct` | 70B | Strong instruction following, tool use |
| `mistralai/Mixtral-8x22B-Instruct-v0.1` | 8x22B | MoE, fits in 282 GB |
| `Qwen/Qwen2.5-72B-Instruct-AWQ` | 72B | AWQ quantized, frees VRAM for second model |

To deploy a different model, edit only `ansible/inventory/group_vars/gpu_nodes/vars.yaml` and
re-run `./scripts/deploy.sh`. Ansible downloads the weights, generates `config.pbtxt` and
`model.json` from templates, and restarts Triton.

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

## Evaluation Steps

1. **Chat model**: Test Qwen 72B qualitatively — German conversation, instruction following, tool use
2. **Embedding model**: Select and deploy on Triton, evaluate retrieval quality on German knowledge base
3. **Verify**: Confirm both models respond correctly via OpenAI-compatible API (`/v1/chat/completions`, `/v1/embeddings`)
4. **Document**: Record chosen models, VRAM usage, and quality assessment

## Acceptance Criteria

- [ ] Chat model evaluated for German quality, instruction following, and tool use
- [ ] Embedding model selected and deployed on Triton (multilingual, works with German text)
- [ ] Both models verified working via OpenAI-compatible API
- [ ] Model choices and rationale documented
- [ ] VRAM usage documented (can both models coexist on 282 GB?)

# Branches
