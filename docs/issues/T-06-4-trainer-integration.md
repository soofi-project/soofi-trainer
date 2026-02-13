# Task

- user story: US-06

# Description

**Soofi Trainer Integration for Local Inference**

Configure the Soofi Trainer stack to connect to an external inference server. This is a config-only change — no new services, just making the endpoint and model configurable.

## Changes

### `.env`
Add new variables with sensible defaults:
```
# Chat model configuration (Cloud — default)
CHAT_MODEL=gpt-4o-mini
OPENAI_API_BASE=https://api.openai.com/v1

# To use local Triton instead:
# CHAT_MODEL=mistral-7b-awq
# OPENAI_API_BASE=https://triton.mrk40.dfki.de/v1
```

### `docker-compose.yml`
Pass `OPENAI_API_BASE` and `CHAT_MODEL` to the agent service.

### README / CLAUDE.md
Document both modes (cloud vs. local) with examples.

## Acceptance Criteria

- [ ] `OPENAI_API_BASE` is configurable via `.env`
- [ ] `CHAT_MODEL` is configurable via `.env`
- [ ] Defaults point to OpenAI (backwards compatible)
- [ ] Switching to Triton requires only `.env` changes
- [ ] README documents both cloud and local configuration
- [ ] CLAUDE.md updated with new env vars

# Branches
