# Task

- user story: #US-07
- depends on: #T-07-1

/label ~UserStory_US-07
/label ~Task
/label ~ToDo

# Description

**Voice Pipeline (Local/Cloud)**

Add speech-to-text (STT) and text-to-speech (TTS) capabilities to the Soofi agent, enabling voice-based interaction through the A2UI frontend.

## Speech-to-Text (STT)

- **Local option**: faster-whisper (CTranslate2-based, runs on CPU for development)
- **Cloud option**: OpenAI Whisper API (for quick development/testing)
- Docker container running the STT service with a simple HTTP API
- Configurable via `.env` (`STT_PROVIDER=local|openai`)

## Text-to-Speech (TTS)

- **Local option**: Piper, Coqui, or F5-TTS (open-source, runs on CPU for development)
- **Cloud option**: OpenAI TTS API (for quick development/testing)
- Docker container running the TTS service with a simple HTTP API
- Configurable via `.env` (`TTS_PROVIDER=local|openai`)
- German voice model required — select a model with good German pronunciation

## Voice Activation

Mic capture is not always-on — it needs an explicit activation trigger. The activation mode is configurable via `VOICE_ACTIVATION` env var:

| Mode | Trigger | Use Case |
|------|---------|----------|
| `push-to-talk` | Keyboard shortcut or physical USB button (HID event) | **Demo setup** (Hannover Messe) — reliable in noisy environments |
| `always-on` | Mic permanently active, no trigger needed | Quiet development/testing |
| `wake-word` | Keyword detection (e.g. "Hey Soofi") | Future option, not implemented initially |

**Push-to-talk** is the primary mode for demo setups. The browser listens for a configurable key/HID event to start/stop mic capture. Options to evaluate:
- Keyboard shortcut (e.g. spacebar, configurable key)
- USB buzzer/button (~10€, sends HID keypress)
- Bluetooth remote

Future: Reachy Mini (if available) could activate the mic via gaze detection (robot detects the user is looking at it and speaking) — this would be handled via Reachy's MCP interface in a separate user story.

## Browser Integration

The full voice pipeline flows through the browser and the Interaction Agent (T-07-6):

```
Activation trigger → Browser mic capture → STT service → text → Interaction Agent → (A2A → specialist agents) → response text → TTS service → audio → Browser playback
```

- Activation event (keypress, USB button, etc.) starts mic capture
- Browser captures microphone audio via Web Audio API
- Audio is sent to the STT service (WebSocket or chunked HTTP POST)
- Transcribed text is sent to the Interaction Agent as a regular message
- The Interaction Agent delegates domain work to specialist agents via A2A as needed
- Response text is sent to the TTS service
- Generated audio is streamed back to the browser for playback
- The `voice-controls` component (T-07-2) provides the UI for this flow (when visible)

## Docker Setup

- Add `stt` and `tts` services to `docker-compose.yml`
- Both services on `soofi-network`
- Health checks for both services
- Volume mounts for local model files (when using local providers)

## Configuration

Add to `.env`:
```
STT_PROVIDER=local          # local | openai
STT_MODEL=large-v3          # faster-whisper model name
TTS_PROVIDER=local          # local | openai
TTS_MODEL=de_DE-thorsten-high  # TTS model/voice name
TTS_LANGUAGE=de
VOICE_ACTIVATION=push-to-talk  # push-to-talk | always-on | wake-word
VOICE_PTT_KEY=Space            # Key for push-to-talk activation
```

Cloud API keys go in `~/.env.secrets` (same pattern as existing OPENAI_API_KEY).

## Acceptance Criteria

- [ ] STT service container runs and transcribes German speech to text
- [ ] TTS service container runs and synthesizes German speech from text
- [ ] Both local and cloud providers are configurable via `.env`
- [ ] Voice activation mode configurable via `VOICE_ACTIVATION` env var
- [ ] Push-to-talk works with keyboard shortcut and/or USB button (HID event)
- [ ] Browser captures microphone audio and sends to STT service
- [ ] Transcribed text is forwarded to the Interaction Agent
- [ ] Interaction Agent response is synthesized to audio and played back in the browser
- [ ] Voice pipeline latency is acceptable for interactive use (<3s round-trip on local)
- [ ] Services added to `docker-compose.yml` with health checks

# Branches

- feature/T-07-3-voice-local
