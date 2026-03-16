# Task

- user story: [US-07](US-07-voice-agent-ui.md)
- depends on: [T-07-1](T-07-1-a2ui-frontend.md)

/label ~UserStory_US-07
/label ~Task
/label ~Done

# Description

**Voice Pipeline (Cloud — OpenAI Whisper + TTS)**

Add speech-to-text (STT) and text-to-speech (TTS) capabilities to the Soofi agent using
OpenAI cloud APIs, enabling voice-based interaction through the A2UI frontend.
Local/H200 providers are handled in [T-07-4](T-07-4-voice-h200.md).

## Architecture

```
Space key / Button
  → MediaRecorder (audio/webm)
  → POST /api/stt/transcribe   (stt service → OpenAI Whisper-1)
  → text → sendMessage()

SSE TEXT_MESSAGE_CONTENT  → text rendered word-by-word
                          → sentence buffer → POST /api/tts/synthesize
                                           → audio/mpeg → Web Audio queue
```

## STT Service (`stt/`)

- OpenAI Whisper-1 via `AsyncOpenAI`
- `POST /transcribe` — multipart `file` (audio/webm)
- `WHISPER_PROMPT` env var biases recognition toward AI/ML domain vocabulary
- STT Refiner: when `voice_input=true`, the Interaction Agent calls `gpt-4o-mini`
  to correct domain ASR errors (e.g. "lora" → "LoRA") before the LangGraph agent runs

## TTS Service (`tts/`)

- OpenAI tts-1 via `AsyncOpenAI`, streaming bytes
- `POST /synthesize` — JSON `{"text": "..."}`
- `TTS_SPEED` env var (default: 1.3)
- `TTS_VOICE` env var (default: alloy)

## Push-to-Talk (Frontend)

- Space key: `keydown`/`keyup` on `window` — works when input field is not focused
- On-screen mic button: hold (push-to-talk) or tap (toggle) — `VITE_VOICE_ACTIVATION`
- Visible only when `VITE_VOICE_CONTROLS_VISIBLE=true` (Docker build arg)

## TTS Playback (Frontend)

- Sentence buffer accumulates `TEXT_MESSAGE_CONTENT` deltas
- Each complete sentence (`.!?` + space) → `cleanForTTS()` → `enqueueTTS()`
- `cleanForTTS()` strips markdown, numbered lists, source section, URLs
- Stops after `TTS_MAX_SENTENCES = 2` — avoids reading the full response aloud
- Audio queue: `fetchAudio()` prefetches while previous clip plays (pipelined)
- TTS starts after the **first sentence** — parallel to continued text streaming
- Queue is cancelled on new message (`ttsGeneration` counter + `currentAudio.pause()`)
- Note: [T-07-7](T-07-7-a2a-status-push.md) will improve voice UX further by having the
  Advisor emit a `speech_intro` ("Ja, ich habe etwas gefunden.") before the first token,
  which would replace the 2-sentence buffer for voice responses

## Stream Delegation (Interaction Agent)

- `ask_advisor_tool` streams Advisor tokens via A2A `send_message_streaming()`
- Each token → `get_stream_writer()` → `on_custom_event` → `TEXT_MESSAGE_CONTENT` SSE
- No second LLM call to reformat the Advisor response
- `advisor_streamed` flag suppresses the Interaction Agent's own LLM output

## Configuration

```
# .env
STT_PROVIDER=openai
STT_LANGUAGE=de
STT_PORT=8010
STT_VERSION=0.1.0
WHISPER_PROMPT=RAG, LoRA, QLoRA, SFT, DPO, Fine-Tuning, LLM, Weaviate, LangGraph, ...

TTS_PROVIDER=openai
TTS_MODEL=tts-1
TTS_VOICE=alloy
TTS_SPEED=1.3
TTS_PORT=8011
TTS_VERSION=0.1.0

VITE_VOICE_CONTROLS_VISIBLE=true
VITE_VOICE_ACTIVATION=push-to-talk   # push-to-talk | toggle
```

## Acceptance Criteria

- [x] STT service (`stt/`) transcribes German speech via OpenAI Whisper-1
- [x] TTS service (`tts/`) synthesizes speech via OpenAI tts-1 (byte streaming)
- [x] Push-to-talk via Space key — fires only when input field is not focused
- [x] On-screen mic button — push-to-talk or toggle mode, configurable via build arg
- [x] Recording indicator (red bar) visible while mic is active
- [x] Searching indicator (animated dots) visible while Advisor tool runs
- [x] Browser captures audio → POST `/api/stt/transcribe` → text → sendMessage()
- [x] `voice_input: true` flag triggers STT Refiner in Interaction Agent
- [x] TTS sentence buffer: playback starts after first sentence, parallel to streaming;
  stops after 2 sentences (`TTS_MAX_SENTENCES`) to avoid reading the full response aloud
- [x] `cleanForTTS()` strips markdown, lists, sources section, URLs
- [x] TTS queue cancelled on new message (`ttsGeneration` counter + `currentAudio.pause()`)
- [x] Stream Delegation: Advisor tokens flow directly to browser without re-generation
- [x] `stt` and `tts` Docker services with health checks and versioned images
- [x] Nginx proxies `/api/stt/` and `/api/tts/`; Vite dev proxies configured
- [x] Advisor sources bug fixed: prompt now correctly references `metadata.source`

# Branches

- feature/T-07-3-voice-local
