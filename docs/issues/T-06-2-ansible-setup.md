# Task

- user story: [US-06](US-06-inference-server.md)

# Description

**Ansible Setup for Inference Server Deployment**

Prepare the Ansible infrastructure for provisioning GPU servers. This covers the tooling and project structure — not the actual server configuration (see [T-06-3](T-06-3-server-provisioning.md)).

Repository: [soofi-inference-server](https://mrk40.dfki.de/soofi/soofi-inference-server)

## Scope

- Create or adapt the Ansible Docker image (based on `soofi-cluster/docker/Dockerfile.ansible`)
- Set up project structure: `ansible/` directory with `site.yaml`, `requirements.yaml`, `ansible.cfg`
- Create inventory template with `[gpu_nodes]` group for lab servers
- Add `deploy.sh` script (`docker run` with Ansible container)
- Document SSH access requirements and prerequisites

## Project Structure

```
soofi-inference-server/
├── ansible/
│   ├── site.yaml                  # Main entrypoint (includes all playbooks)
│   ├── requirements.yaml          # Ansible Galaxy roles + collections
│   ├── ansible.cfg
│   └── inventory/
│       └── hosts.yaml             # GPU server inventory ([gpu_nodes])
├── docker/
│   ├── Dockerfile.ansible         # Ansible runner container
│   └── docker-compose.yml         # Triton stack (existing, moved here)
├── deploy.sh                      # docker run with Ansible container
└── ...
```

## Ansible Docker Image

Extend the soofi-cluster Ansible image with:
- No Kubernetes tooling needed (no kubectl, helm, kubeseal)
- Add Docker Compose support for remote deployment
- Keep: ansible-core, SSH client, Python basics

## Acceptance Criteria

- [ ] Ansible Docker image builds successfully
- [ ] Project structure follows soofi-cluster conventions
- [ ] Inventory template with `[gpu_nodes]` group exists
- [ ] `deploy.sh` runs `docker run` with the Ansible container to execute playbooks
- [ ] README documents SSH prerequisites and usage

# Branches
