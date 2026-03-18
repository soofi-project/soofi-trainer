# Task

- user story: [US-06](US-06-inference-server.md)
- depends on: [T-06-6](T-06-6-local-inference.md)

/label ~UserStory_US-06
/label ~Task
/label ~ToDo

# Description

**LLM Settings: Temperature, Model Parameters & Inference Tuning**

All three LangGraph agents (Advisor, Interaction Agent, Training Agent) use `ChatOpenAI()` without explicit inference parameters — provider defaults apply (e.g. `temperature=1.0` on OpenAI, undefined on vLLM/LiteLLM). For the demo and production use, sensible values must be set and made configurable.

Additionally, the vLLM server-side configuration needs review: thinking/reasoning is currently enabled by default (Qwen 3.5 produces `<think>` blocks), MTP speculative decoding is unstable, and alternative models should be evaluated.

## Current State

### Agent-Side (Soofi Trainer)

| Agent | Code | Parameters |
|-------|------|------------|
| Advisor | `advisor/src/graph.py:27` | `ChatOpenAI(model=model)` — no temperature, no max_tokens |
| Interaction Agent | `interaction-agent/src/graph.py:314` | `ChatOpenAI(model=model_name)` — no temperature, no max_tokens |
| Training Agent | `training-agent/src/training_agent/graph.py:26` | `ChatOpenAI(model=model)` — no temperature, no max_tokens |

None of the agents set `temperature`, `top_p`, `max_tokens`, or any other inference parameter.

### Server-Side (H200 / vLLM)

Current vLLM config for `qwen35-122b-fp8` (from `ansible/inventory/group_vars/gpu_nodes/vars.yaml`):

| Parameter | Value | Notes |
|-----------|-------|-------|
| `gpuMemoryUtilization` | `0.93` | ~130 GB model on 141 GB H200, leaves ~11 GB for KV cache |
| `maxModelLen` | `16384` | Conservative (model supports 262K) — limited by VRAM |
| `enablePrefixCaching` | `true` | Reuses KV cache across requests with shared prefixes |
| `enableChunkedPrefill` | `false` | Minimal benefit at `max_num_seqs=4` |
| `swap-space` | `16` GB | CPU swap for KV cache overflow |
| `max-num-seqs` | `4` | Max concurrent sequences — limited by VRAM budget |
| `reasoning-parser` | `qwen3` | Parses `<think>` blocks into `reasoning_content` field |
| `tool-call-parser` | `qwen3_coder` | Enables auto tool calling for Qwen 3.5 |

**Problem:** `--reasoning-parser qwen3` does NOT control whether the model thinks — it only parses the output. Qwen 3.5's chat template has thinking **enabled by default**, so the model produces `<think>...</think>` blocks on every response, consuming tokens and latency.

---

## Tasks

### 1. Disable Thinking by Default on vLLM

Add to the vLLM launch command (in `vars.yaml` extraArgs):
```
--default-chat-template-kwargs '{"enable_thinking": false}'
```

This makes non-thinking the default. Individual requests can opt-in with `{"enable_thinking": true}` if needed.

**Why:** With `max_model_len=16384`, thinking wastes context budget. Qwen recommends 128K+ to preserve thinking quality — at 16K, thinking output is likely truncated and unhelpful. For a RAG + tool-calling agent, factual answers without reasoning traces are preferred.

**Known issue:** vLLM issue #35574 reports that `enable_thinking: false` may not work reliably in some vLLM versions. Test after applying and upgrade vLLM if necessary.

**Per-request control (LangChain):**
```python
llm = ChatOpenAI(
    model=model,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}}
)
```

### 2. Remove MTP Speculative Decoding

The commented-out config includes `"speculative-config": '{"method": "mtp", "num_speculative_tokens": 1}'`. This should **not** be enabled for Qwen3.5-122B:

- vLLM issue #36031: Crashes with Qwen3.5-122B + MTP
- vLLM issue #36331: 0% acceptance rate (no speedup at all)
- vLLM issue #35800: MTP causes malformed tool calls

MTP works on smaller Qwen3.5 variants (27B) but is unstable on 122B as of vLLM v0.17. Remove the commented-out speculative config to avoid confusion.

### 3. Temperature & Sampling Parameters per Agent

Add environment variables to `.env` with sensible defaults:

```env
# --- Advisor ---
ADVISOR_TEMPERATURE=0.3

# --- Interaction Agent ---
INTERACTION_TEMPERATURE=0.5

# --- Training Agent ---
TRAINING_AGENT_TEMPERATURE=0.3
```

Pass to `ChatOpenAI()`:
```python
llm = ChatOpenAI(
    model=model,
    temperature=float(os.getenv("ADVISOR_TEMPERATURE", "0.3")),
)
```

Recommended values:

| Agent | Temperature | Rationale |
|-------|------------|-----------|
| Advisor | `0.2–0.4` | RAG-based answers should be factual, minimal creative variation |
| Interaction Agent | `0.4–0.6` | Conversational but must call tools reliably |
| Training Agent | `0.2–0.3` | Technical decisions (hyperparameters, methods) — accuracy critical |

### 4. Model Selection: Alternatives for 2x H200 (282 GB)

Current: Only GPU 0 runs the chat model (Qwen3.5-122B, ~130 GB). GPU 1 runs embedding (Qwen3-Embedding-8B, ~50%) + STT (faster-whisper, ~3 GB). There is room for a second chat model or a larger one across both GPUs.

**Viable alternatives:**

| Model | Total / Active Params | FP8 Size | GPUs Needed | Tool Calling | German Quality | Notes |
|-------|-----------------------|----------|-------------|-------------|----------------|-------|
| **Qwen3.5-122B-A10B-FP8** (current) | 122B / 10B MoE | ~130 GB | 1x H200 | Yes (qwen3_coder) | Excellent | Best efficiency — leaves GPU 1 free |
| **Llama 4 Maverick 17B-128E** | 400B / 17B MoE | ~400 GB | 2x H200 (PP=2) | Yes (pythonic) | Good | Largest model that fits; needs pipeline parallelism (PCIe, no NVLink) |
| **Mistral Large 2 (123B)** | 123B dense | ~130 GB | 2x H200 (TP=2) | Yes (mistral) | Good | Mature tool calling; dense = higher per-token quality but slower |
| **Qwen3-235B-A22B** | 235B / 22B MoE | ~250 GB | 2x H200 | Yes | Excellent | Tight fit — minimal KV cache room, short context only |
| **Command-R+ (104B)** | 104B dense | ~110 GB | 1–2x H200 | Yes (native RAG) | Good | Built-in RAG grounding; Cohere license restrictions |

**Do not consider** (too large): DeepSeek V3/R1 (671B, needs 8+ GPUs), Qwen3.5-397B.

**Recommendation:** Stay with Qwen3.5-122B for now — it is the best fit for single-GPU efficiency with excellent German and tool calling. Llama 4 Maverick is worth evaluating if GPU 1 becomes available (currently used by embedding + STT).

Evaluate whether per-agent models make sense:
- **Advisor**: Needs strong German + RAG → 122B
- **Training Agent**: Mostly tool calls → could use a smaller model (35B) if deployed on GPU 1
- **Interaction Agent**: Orchestrator, must reliably delegate → 122B

### 5. vLLM Server-Side Tuning

Review and document these parameters:

| Parameter | Current | Recommendation | Notes |
|-----------|---------|----------------|-------|
| `gpuMemoryUtilization` | `0.93` | Keep at 0.93 | ~11 GB left for KV cache on 141 GB H200 |
| `maxModelLen` | `16384` | Consider `32768` if KV cache allows | Monitor `vllm:gpu_cache_usage_perc` via `/metrics` |
| `max-num-seqs` | `4` | Test `8` with monitoring | Low value limits throughput; increase if KV cache usage stays below 80% |
| `enableChunkedPrefill` | `false` | Test `true` | Minimal impact at low concurrency, but may improve latency for long prompts |
| `swap-space` | `16` | Keep | CPU swap for KV cache overflow — 16 GB is generous with 256 GB system RAM |
| `enablePrefixCaching` | `true` | Keep | Beneficial for RAG (shared system prompt + similar queries) |

**Monitoring:** Check `curl http://10.2.10.33:8001/metrics | grep gpu_cache_usage` to see if KV cache is a bottleneck before increasing `max_model_len` or `max_num_seqs`.

---

## Files to Change

### Soofi Trainer (this repo)
- `advisor/src/graph.py` — Add temperature to `ChatOpenAI()`
- `interaction-agent/src/graph.py` — Add temperature to `ChatOpenAI()`
- `training-agent/src/training_agent/graph.py` — Add temperature to `ChatOpenAI()`
- `.env` — New `*_TEMPERATURE` variables
- `docker-compose.yml` — Forward new env vars to containers
- `docker-compose.vllm.yml` — Model-specific overrides if per-agent models are used
- `README.md` — Document new configuration variables

### Inference Server (soofi-inference-server)
- `ansible/inventory/group_vars/gpu_nodes/vars.yaml` — Add `--default-chat-template-kwargs`, remove MTP comments, tune `max_model_len` / `max_num_seqs`

---

# Acceptance Criteria

- [ ] Thinking is disabled by default on vLLM (`--default-chat-template-kwargs '{"enable_thinking": false}'`)
- [ ] Verified that thinking is actually off (no `<think>` blocks in responses)
- [ ] All three agents have configurable `temperature` via environment variable
- [ ] Sensible default values are set and documented
- [ ] Temperature values are tested with the current model (Qwen 3.5 122B)
- [ ] Decision documented whether per-agent model selection is worthwhile
- [ ] MTP speculative decoding config removed (unstable for 122B)
- [ ] `max_model_len` and `max_num_seqs` reviewed based on KV cache metrics
- [ ] README documents new configuration variables
