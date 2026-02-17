# Task

- user story: [US-07](US-07-voice-agent-ui.md)
- depends on: [T-07-3](T-07-3-voice-local.md)

/label ~UserStory_US-07
/label ~Task
/label ~ToDo

# Description

**Voice on H200 (Production)**

Deploy the STT and TTS models on the H200 GPU server for production-grade voice processing with low latency. Builds on the local/cloud voice pipeline from [T-07-3](T-07-3-voice-local.md).

## GPU-Optimized Inference

### STT (faster-whisper)
- CTranslate2 backend with CUDA support on H200
- Use `large-v3` model for best German transcription quality
- Batch processing support for concurrent requests
- Target latency: <500ms for typical utterances

### TTS
- GPU-accelerated inference for the selected TTS model
- Streaming audio generation where supported
- German voice model optimized for natural prosody
- Target latency: <1s for typical responses

## Ansible Deployment

- Ansible playbooks following the same patterns as [US-06](US-06-inference-server.md) infrastructure
- Playbooks for:
  - STT model download and container deployment
  - TTS model download and container deployment
  - NVIDIA container runtime configuration (if not already done by [US-06](US-06-inference-server.md))
  - Health checks and monitoring setup
- Integration with existing server provisioning (same H200 server, same Ansible inventory)

## Production Configuration

- `.env.production` overrides for voice services (model paths, GPU device IDs, batch sizes)
- Resource limits (GPU memory allocation) to coexist with inference models from [US-06](US-06-inference-server.md)
- Logging and monitoring integration

## Model Selection for German

Evaluate and select models with the best German language support:
- STT: faster-whisper `large-v3` (strong German support out of the box)
- TTS: Compare Piper (de_DE-thorsten), F5-TTS, and Coqui XTTS for German quality

## Acceptance Criteria

- [ ] STT runs on H200 with GPU acceleration (CUDA)
- [ ] TTS runs on H200 with GPU acceleration
- [ ] Ansible playbooks deploy both services to the H200 server
- [ ] Playbooks follow existing [US-06](US-06-inference-server.md) Ansible patterns
- [ ] STT transcription latency <500ms for typical German utterances
- [ ] TTS synthesis latency <1s for typical German responses
- [ ] Voice services coexist with inference models (resource limits configured)
- [ ] German language quality validated for both STT and TTS

# Branches

- feature/T-07-4-voice-h200
