# Task

- user story: [US-06](US-06-inference-server.md)

# Description

**Soofi Trainer Integration for Local Inference**

Configure the Soofi Trainer stack to connect to an external inference server. This is a config-only
change — no new services, just making the endpoint and model configurable.

## Changes

### `.env`
Add new variables with sensible defaults:
```
# Chat model configuration (Cloud — default)
CHAT_MODEL=gpt-4o-mini
OPENAI_API_BASE=https://api.openai.com/v1

# To use local Triton instead:
# CHAT_MODEL=qwen2.5-72b
# OPENAI_API_BASE=http://10.2.10.33:9000/v1
```

### `docker-compose.yml`
Pass `OPENAI_API_BASE` and `CHAT_MODEL` to the agent service.

### README / CLAUDE.md
Document all three modes (cloud, Triton, local Ollama/LM Studio) with examples.

## Acceptance Criteria

- [ ] `OPENAI_API_BASE` is configurable via `.env`
- [ ] `CHAT_MODEL` is configurable via `.env`
- [ ] Defaults point to OpenAI (backwards compatible)
- [ ] Switching to Triton requires only `.env` changes
- [ ] README documents cloud, Triton, and local configuration
- [ ] CLAUDE.md updated with new env vars

# Branches
