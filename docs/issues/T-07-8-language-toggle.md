# Task

- user story: [US-07](US-07-voice-agent-ui.md)
- depends on: [T-07-6](T-07-6-interaction-agent.md), [T-07-7](T-07-7-a2a-status-push.md)

/label ~UserStory_US-07
/label ~Task
/label ~ToDo

# Description

**Runtime Language Toggle (DE/EN)**

At Hannover Messe the Soofi demo must be switchable to English on the fly, without
restarting the stack. A toggle in the UI header switches the language per request.

## RAG Compatibility

- **Embedding** (`text-embedding-3-large`, target: `Qwen3-Embedding-8B`): multilingual —
  cross-lingual search (EN query → DE docs) works out of the box.
- **Reranker** (planned T-02-3, target: `Qwen3-Reranker-4B`): also multilingual (100+ languages).
- **Knowledge documents stay German** — no duplication needed.
- The Advisor LLM answers in the requested language based on German sources.

## Language Propagation

```
UI Toggle (DE/EN)
  → POST /agent { language: "de"|"en", messages, session_id }
    → interaction-agent: ContextVar + prompt selection
      → ask_advisor_tool: appends [LANG:en] to question
        → advisor a2a_handler: extracts [LANG:xx], selects prompt
      → ask_training_agent_tool: same pattern
```

## Scope

### New Files (4)

| File | Content |
|------|---------|
| `soofi-ui/src/i18n.ts` | ~15 UI strings (de/en) + `tr()` helper |
| `interaction-agent/src/i18n.py` | ~15 backend strings (de/en) + `tr()` helper |
| `advisor/src/i18n.py` | 2 strings (search_status, processing_error) |
| `training-agent/src/training_agent/i18n.py` | 1 string (calling_gateway) |

### Modified Files

**Frontend:**
- `soofi-ui/src/main.ts`: Toggle button in header, `language` state, `language` in request body,
  all German strings → `tr("key", this.language)`

**Interaction Agent:**
- `prompts.py`: `SYSTEM_PROMPT` → `SYSTEM_PROMPT_DE` + `SYSTEM_PROMPT_EN`
- `graph.py`: New `ContextVar` `_language`, `set_language()`, prompt selection
  in `agent()`, `[LANG:xx]` appended to A2A calls, tool return labels via `tr()`
- `agent.py`: Extract `language` from request, call `set_language()`, pass `language` to `SSEStream`
- `sse_stream.py`: `language` param in constructor, error message via `tr()`
- `speech.py`: `lang` param in `generate_speech_text()`, fallback string via `tr()`

**Advisor:**
- `prompts.py`: + `SYSTEM_PROMPT_EN`
- `graph.py`: System prompt from `config["configurable"]["system_prompt"]`
- `a2a_handler.py`: `[LANG:xx]` extraction from message, prompt selection, pass via config

**Training Agent:**
- `prompts.py`: + `SYSTEM_PROMPT_EN`
- `graph.py`: System prompt from config
- `a2a_handler.py`: `[LANG:xx]` extraction + prompt selection

**Agent Cards (all 3 services):**
- Bilingual descriptions and skill names as `{"de": "...", "en": "..."}`
- `?lang=xx` query param on agent card endpoint

### Not Changed
- Knowledge documents remain German (cross-lingual search)
- Vector MCP, Weaviate, Knowledge Ingestion — language-independent

## Acceptance Criteria

1. Start stack, toggle DE → ask a domain question → German answer with **Quellen**
2. Toggle EN → same question → English answer with **Sources**, German source docs
3. Start training job on EN → English status labels and response
4. Open agent cards on EN → English descriptions and skill names
5. Mid-conversation language switch → next answer in new language
