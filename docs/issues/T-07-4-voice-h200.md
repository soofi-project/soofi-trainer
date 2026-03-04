# Task

- user story: [US-07](US-07-voice-agent-ui.md)
- depends on: [T-07-3](T-07-3-voice-local.md)

/label ~UserStory_US-07
/label ~Task
/label ~ToDo

# Description

**Voice on H200 (Local/Production)**

Replace the OpenAI cloud STT/TTS APIs with local models running on the H200 GPU server.
No internet connection required. Builds on the voice pipeline from [T-07-3](T-07-3-voice-local.md).

## STT: faster-whisper-server

Replace OpenAI Whisper-1 with a local `faster-whisper-server` instance. This server exposes
an **OpenAI-compatible API** (`/v1/audio/transcriptions`) — so `stt/src/server.py` requires
no code change. Only two env vars change:

```
STT_BASE_URL=http://faster-whisper:8000   # instead of https://api.openai.com
STT_API_KEY=unused                         # local server, no key needed
```

- Model: `large-v3` — best German transcription quality (CTranslate2 + CUDA on H200)
- Target latency: <500ms for typical utterances
- Same `/transcribe` endpoint, same multipart format

## TTS: Piper

Replace OpenAI TTS with [Piper](https://github.com/rhasspy/piper) — a fast, local neural
TTS engine with good German support. Piper does NOT expose an OpenAI-compatible API, so
`tts/src/server.py` needs a `TTS_PROVIDER=piper` branch.

Piper is called via subprocess or HTTP (piper-server):
```python
# TTS_PROVIDER=piper
result = subprocess.run(
    ["piper", "--model", TTS_MODEL, "--output_raw"],
    input=text.encode(),
    capture_output=True,
)
# stream raw PCM → convert to mp3 or serve as audio/wav
```

German voice model options (evaluate quality before committing):
- `de_DE-thorsten-high` — male, good quality
- `de_DE-kerstin-low` — female, faster
- `de_DE-thorsten_emotional-medium` — male, more expressive

## Ansible Deployment

Following the same patterns as [US-06](US-06-inference-server.md):

- Playbook: download faster-whisper model (`large-v3`) to H200 volume
- Playbook: download Piper voice model to H200 volume
- NVIDIA container runtime already configured by US-06
- Resource limits: allocate GPU memory alongside inference models from US-06
- Health checks and monitoring integration

## Configuration

```
# .env (H200 overrides)
STT_PROVIDER=local
STT_BASE_URL=http://faster-whisper:8000
STT_API_KEY=unused

TTS_PROVIDER=piper
TTS_MODEL=/models/de_DE-thorsten-high.onnx
TTS_VOICE=de_DE-thorsten-high
```

## Acceptance Criteria

- [ ] `stt/src/server.py` supports `STT_BASE_URL` env var to redirect to local faster-whisper-server
- [ ] faster-whisper-server Docker service runs on H200 with CUDA (`large-v3` model)
- [ ] STT transcription latency <500ms for typical German utterances on H200
- [ ] `tts/src/server.py` supports `TTS_PROVIDER=piper` with subprocess/piper-server backend
- [ ] Piper Docker service runs on H200 with German voice model
- [ ] TTS synthesis latency <1s for typical German responses on H200
- [ ] Ansible playbooks deploy both services to H200 (model download + container start)
- [ ] Playbooks follow existing US-06 Ansible patterns
- [ ] Voice services coexist with inference models (GPU memory limits configured)
- [ ] German voice quality validated for both STT and TTS

# Branches

- feature/T-07-4-voice-h200
