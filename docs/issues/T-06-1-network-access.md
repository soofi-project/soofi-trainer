# Task

- user story: [US-06](US-06-inference-server.md)

# Description

**Network Access & Connectivity**

Ensure the GPU server in the data center is reachable from the development environment and ready for
Ansible provisioning. This is a prerequisite for all other tasks in this user story.

Repository: [soofi-inference-server](https://mrk40.dfki.de/soofi/soofi-inference-server)

## Scope

### Data Center Access

The H200 server is located in the data center. Physical access is required to:
- Boot the server and verify hardware (GPUs, storage, network)
- Connect to the lab network
- Ensure the server is reachable via VPN from outside

### Network Connectivity

| Port | Protocol | Purpose | Direction |
|------|----------|---------|-----------|
| 22 | TCP | SSH (Ansible provisioning) | Dev machine → GPU server |
| 8000 | TCP | Triton KServe V2 HTTP | Clients → GPU server |
| 8001 | TCP | Triton gRPC | Clients → GPU server |
| 8002 | TCP | Triton Metrics (Prometheus) | Monitoring → GPU server |
| 9000 | TCP | Triton OpenAI-compatible API | Clients → GPU server |

Access is via VPN + direct IP (`10.2.10.33`). UFW firewall rules are managed by Ansible
([T-06-3](T-06-3-server-provisioning.md), `os_setup.yaml`).

### Optional: DNS & Reverse Proxy

For production use, a DNS entry (e.g. `triton.mrk40.dfki.de`) with TLS termination via reverse
proxy would be desirable but is not required for the current lab setup.

## Acceptance Criteria

- [x] SSH access from development machine to GPU server works
- [x] GPU server reachable via VPN from outside the lab
- [x] Triton ports (8000, 9000) accessible from the Trainer network
- [ ] Server physically set up in the data center and connected to the lab network

# Branches
