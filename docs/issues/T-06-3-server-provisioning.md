# Task

- user story: US-06

# Description

**Server Provisioning Playbooks**

Create the Ansible playbooks that configure a bare GPU server from scratch. This task uses the Ansible setup from T-06-2 and writes the actual provisioning logic.

Repository: [soofi-inference-server](https://mrk40.dfki.de/soofi/soofi-inference-server)

## Playbooks

### 1. OS Base (`os_setup.yaml`)
- System packages, NTP, firewall rules
- OS-independent via `ansible.builtin.package`
- Create service user for Docker

### 2. NVIDIA Stack (`nvidia_setup.yaml`)
- NVIDIA driver (latest stable)
- CUDA Toolkit
- NVIDIA Container Toolkit
- Use existing Ansible Galaxy roles where available (e.g. `nvidia.nvidia_driver`)
- Verify installation: `nvidia-smi` check

### 3. Docker (`docker_setup.yaml`)
- Docker Engine + Docker Compose plugin
- Configure NVIDIA runtime as default
- Add service user to docker group

### 4. Triton Deployment (`triton_deploy.yaml`)
- Copy `docker-compose.yml` to server
- Pull Triton image
- Download model(s) from HuggingFace
- Start Triton via Docker Compose
- Health check: `/v2/health/ready`

## Target Hardware

- 2x NVIDIA H200 (141 GB HBM3e each, 282 GB total)
- CPU: 2x AMD EPYC GENOA 9124
- RAM: 256 GB
- Storage: 3.84 TB SSD

## Acceptance Criteria

- [ ] Fresh server can be provisioned with `./deploy.sh`
- [ ] NVIDIA driver + CUDA + Container Toolkit installed idempotently
- [ ] Works on Ubuntu 24.04 (primary), adaptable to RHEL-based distros
- [ ] Docker configured with NVIDIA runtime
- [ ] Triton + vLLM running and serving models
- [ ] Health check passes (`/v2/health/ready`)
- [ ] Playbooks are idempotent (re-run without side effects)

# Branches
