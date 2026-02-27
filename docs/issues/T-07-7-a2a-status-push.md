# Task

- user story: [US-07](US-07-voice-agent-ui.md)
- depends on: [T-07-6](T-07-6-interaction-agent.md)

/label ~UserStory_US-07
/label ~Task
/label ~ToDo

# Description

**Async A2A Status Push (Advisor → Interaction Agent)**

Currently the Interaction Agent polls implicitly — it sends a question to the Advisor via A2A and
waits for the full response. During the RAG search (vector lookup + LLM generation) the Interaction
Agent has no visibility into what the Advisor is doing, and the browser shows a generic "searching"
indicator.

This task adds **intermediate status events** that the Advisor pushes back to the Interaction
Agent during processing, enabling more granular progress feedback in the UI.

## Current Flow

```
Interaction Agent  →  A2A send_message  →  Advisor
                                               ↓
                                        [RAG search + LLM]
                                               ↓
Interaction Agent  ←  A2A response      ←  Advisor
```

The `stream_advisor()` client already uses `send_message_streaming()` and receives
`TaskStatusUpdateEvent(state=working)` chunks as the Advisor LLM streams tokens. This part works.

## What's Missing

The Advisor does not emit status events *before* the LLM starts generating — i.e. during the
`search_documents` tool call (Weaviate lookup). The user therefore sees no feedback for ~1–3
seconds before the first token arrives.

## Proposed Solution

### 1. Pre-retrieval status (visual)

In `advisor/src/graph.py`, before calling `search_documents`, the Advisor emits a working-state
status update via the LangGraph streaming mechanism (e.g. `get_stream_writer()` or a custom
A2A status event), so the Interaction Agent receives it as a `TaskStatusUpdateEvent` during
`send_message_streaming()`.

Example status messages (German):
- `"Suche in der Wissensdatenbank…"` — before `search_documents` tool call
- `"Analysiere Ergebnisse…"` — after retrieval, before LLM generation starts

The Interaction Agent forwards these as labeled `TOOL_CALL_START` events so the UI can show
more specific feedback than the current generic indicator.

### 2. Post-retrieval speech intro (voice UX)

After `search_documents` completes, the Advisor knows immediately whether relevant results
were found. Before the LLM starts generating the full answer, it emits a short spoken intro
as a special status event:

```json
{ "type": "speech_intro", "text": "Ja, ich habe etwas gefunden." }
```
or, if nothing was found:
```json
{ "type": "speech_intro", "text": "Leider habe ich dazu nichts in meiner Wissensdatenbank." }
```

The Interaction Agent forwards this as a new SSE event `SPEECH_INTRO` to the browser, which
immediately calls TTS — **before the first content token arrives**. This gives the user an
immediate spoken acknowledgement that the system has processed their question, while the full
answer is still being generated.

Note: a spoken "Ich suche..." at TOOL_CALL_START is **not** implemented. Synthesis + playback
of even a short clip takes ~1s, which on fast hardware (H200: <400ms search) would overlap
awkwardly with the first answer sentence. The visual indicator already covers this gap.

## Implementation Notes

- The A2A streaming path (`send_message_streaming` → `TaskStatusUpdateEvent(state=working)`)
  is already wired end-to-end. Changes are only on the **Advisor side**.
- Requires LangGraph streaming from within a tool node. Evaluate whether
  `langgraph.config.get_stream_writer()` works inside `search_documents` tool or whether a
  different mechanism is needed.
- Interaction Agent (`agent.py`) distinguishes status-only chunks from content chunks by event
  type key, and routes `speech_intro` directly to TTS via a new `SPEECH_INTRO` SSE event.
- Should be backward-compatible: if the Advisor does not emit pre-retrieval status, the
  Interaction Agent falls back to the current generic indicator.

## Acceptance Criteria

- [ ] Advisor emits a status event before `search_documents` completes (visual feedback)
- [ ] Interaction Agent receives the event via `send_message_streaming()`
- [ ] Browser UI shows a specific label (e.g. "Suche in Wissensdatenbank…") during retrieval
- [ ] Advisor emits `speech_intro` event after retrieval, before LLM generation
- [ ] Browser receives `SPEECH_INTRO` SSE event and immediately calls TTS
- [ ] Voice user hears spoken acknowledgement before first content sentence
- [ ] No regression in streaming quality or latency
- [ ] Backward-compatible: Interaction Agent handles advisors that do not emit these events

# Branches

- feature/T-07-7-a2a-status-push
