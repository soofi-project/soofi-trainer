# Task

- user story: US-06

# Description

**Network Access & Connectivity**

Ensure the GPU server in the data center is reachable from the Soofi Trainer development environment. This is a prerequisite for all other tasks in this user story.

Repository: [soofi-inference-server](https://mrk40.dfki.de/soofi/soofi-inference-server)

## Scope

- DNS entry for the GPU server (e.g. `triton.mrk40.dfki.de`)
- Reverse proxy with TLS termination (HTTPS)
- Firewall rules: allow HTTPS (443) from Trainer network, SSH (22) for Ansible
- SSH access for Ansible provisioning (T-06-2 depends on this)
- Connectivity test: verify Triton API is reachable via `https://triton.mrk40.dfki.de/v2/health/ready`

## Network Requirements

| Port | Protocol | Purpose | Direction |
|------|----------|---------|-----------|
| 22 | TCP | SSH (Ansible provisioning) | Trainer → GPU Server |
| 443 | TCP | HTTPS (Reverse proxy → Triton) | Trainer → GPU Server |
| 8000 | TCP | Triton HTTP API (internal, behind proxy) | Reverse Proxy → Triton |
| 8001 | TCP | Triton gRPC API (internal) | Internal only |
| 8002 | TCP | Triton Metrics (internal) | Internal only |

## Acceptance Criteria

- [ ] GPU server has a DNS name (e.g. `triton.mrk40.dfki.de`)
- [ ] Reverse proxy with TLS termination is configured
- [ ] SSH access from development machine to GPU server works
- [ ] Triton API reachable via HTTPS from the Trainer network
- [ ] Connectivity verified: `curl https://triton.mrk40.dfki.de/v2/health/ready`

# Branches
