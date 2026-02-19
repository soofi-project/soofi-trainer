# Task

- user story: [US-06](US-06-inference-server.md)

# Description

**Server Provisioning Playbooks**

Create the Ansible playbooks that configure a bare GPU server from scratch. This task uses the Ansible setup from [T-06-2](T-06-2-ansible-setup.md) and writes the actual provisioning logic.

Repository: [soofi-inference-server](https://mrk40.dfki.de/soofi/soofi-inference-server)

## Playbooks

### 1. OS Base (`os_setup.yaml`)
- System packages (build-essential, curl, wget, git, htop, nvme-cli, net-tools, vim), NTP, UFW firewall
- UFW rules: allow SSH (22) + Triton ports (8000/8001/8002/9000) before enabling
- System limits (nofile 1048576, memlock unlimited) and swap disabled

### 2. NVIDIA Stack (`nvidia_setup.yaml`)
- CUDA repo added first (590-server driver lives there, not in Ubuntu default repo)
- `nvidia-driver-590-server` — skipped if `nvidia-smi` already works (idempotent precheck)
- NVIDIA Container Toolkit + `nvidia-ctk runtime configure --runtime=docker`
- CUDA Toolkit optional via `install_cuda_toolkit` variable (not needed for Docker workloads)

### 3. Docker (`docker_setup.yaml`)
- Docker Engine + Compose plugin (skip if already installed)
- NVIDIA runtime set as Docker default runtime
- `mrk` added to `docker` group

### 4. Triton Deployment (`triton_deploy.yaml`)
- Deploys docker-compose.yml, litellm-config.yaml, triton-start.sh
- Templates `.env` from `triton.env.j2` with vault secrets
- **Model config from single source**: `model_name` + `triton_model_name` in `group_vars/gpu_nodes/vars.yaml`
  drive both `config.pbtxt` and `model.json` via Jinja2 templates — no hardcoded values anywhere
- **Explicit model pre-download**: `huggingface-cli download` runs inside the Triton container before
  `docker compose up`, so the health check is not blocked by a multi-hour initial download
- Health check: `/v2/health/ready` (retries: 40 x 30s after 300s grace period = up to 25 min)

### 5. Triton Startup (`docker/triton-start.sh`)
- Locates the OpenAI-compatible frontend in the Triton image at runtime
- Starts Triton with `--enable-kserve-frontends`: KServe V2 on port 8000 (LiteLLM) + OpenAI API on port 9000 (direct clients)
- Falls back to plain `tritonserver` if the frontend is not found

## Secrets & Configuration

All secrets (`hf_token`, `litellm_master_key`, `ansible_become_password`) are stored in
`ansible/inventory/group_vars/gpu_nodes/vault.yaml` (Ansible Vault, AES256).
Non-secret deployment settings live in `vars.yaml` in the same directory.

**To change the model** — edit only `vars.yaml`:
```yaml
models:
  - hf_name: "Qwen/Qwen2.5-72B-Instruct"   # HuggingFace model ID
    triton_name: "qwen2.5-72b"              # Triton model directory name
    # quantization: "awq"                   # uncomment for AWQ models
```
Multiple models are supported — each entry gets its own `config.pbtxt`, `model.json`, and download step.

## Target Hardware

- 2x NVIDIA H200 NVL (141 GB HBM3e each, 282 GB total)
- CPU: 2x AMD EPYC GENOA 9124
- RAM: 256 GB
- Storage: 3.84 TB SSD

## Acceptance Criteria

- [x] Fresh server can be provisioned with `./scripts/deploy.sh`
- [x] NVIDIA driver 590-server + Container Toolkit installed idempotently
- [x] Works on Ubuntu 24.04
- [x] Docker configured with NVIDIA runtime as default
- [x] Triton + vLLM running and serving models via Docker Compose
- [x] OpenAI-compatible API exposed on port 9000 (`triton-start.sh`)
- [x] KServe V2 endpoint remains on port 8000 for LiteLLM
- [x] Health check passes (`/v2/health/ready`)
- [x] Playbooks are idempotent (re-run without side effects)
- [x] Model configured in one place (`vars.yaml`) — no duplication across `model.json` / `config.pbtxt` / env
- [x] Model weights pre-downloaded by Ansible before Triton starts

# Branches

- `feature/T-06-3-server-provisioning`
