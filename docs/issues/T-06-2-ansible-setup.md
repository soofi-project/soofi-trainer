# Task

- user story: [US-06](US-06-inference-server.md)

# Description

**Ansible Setup for Inference Server Deployment**

Prepare the Ansible infrastructure for provisioning GPU servers. This covers the tooling and project
structure — not the actual server configuration (see [T-06-3](T-06-3-server-provisioning.md)).

Repository: [soofi-inference-server](https://mrk40.dfki.de/soofi/soofi-inference-server)

## Scope

- Ansible Docker image (`docker/Dockerfile.ansible`) with ansible-core, SSH client, Galaxy collections
- Long-running container pattern: `docker compose up -d` + `docker compose exec` (not `docker run`)
- `ansible-run.sh` wrapper: fixes SSH permissions on Windows (NTFS 0777) and Linux (UID mismatch),
  strips macOS-only SSH options, starts SSH agent, loads keys
- Project structure: `ansible/` with `site.yaml`, `ansible.cfg`, `requirements.yaml`, inventory
- `scripts/deploy.sh` — single entrypoint for deployments (starts container, runs playbooks)
- `scripts/edit-vault.sh` — Ansible Vault management (encrypt, edit secrets)
- Ansible Vault for secrets (`hf_token`, `litellm_master_key`, `ansible_become_password`)

## Project Structure

```
soofi-inference-server/
├── ansible/
│   ├── site.yaml                      # Orchestrator (imports all playbooks)
│   ├── ansible.cfg                    # SSH args, pipelining, host_key_checking
│   ├── requirements.yaml              # Galaxy collections (community.docker, community.general)
│   ├── templates/                     # Jinja2 templates for server-side configs
│   ├── playbooks/                     # Provisioning playbooks (see T-06-3)
│   └── inventory/
│       ├── hosts.yaml                 # GPU server inventory [gpu_nodes]
│       └── group_vars/gpu_nodes/
│           ├── vars.yaml              # Non-secret deployment settings
│           └── vault.yaml             # Secrets (AES256-encrypted)
├── docker/
│   ├── Dockerfile.ansible             # Ansible runner container
│   ├── ansible-run.sh                 # SSH/permissions wrapper
│   ├── docker-compose.ansible.yml     # Ansible runner service
│   └── docker-compose.yml             # Triton stack
├── scripts/
│   ├── deploy.sh                      # Deployment entrypoint
│   └── edit-vault.sh                  # Vault management
└── ...
```

## Ansible Docker Image

Based on `python:3.11-slim`:
- ansible-core, docker, requests (pip)
- community.docker, community.general (Galaxy)
- openssh-client, sshpass, git, vim
- No Kubernetes tooling (kubectl, helm, kubeseal not needed)

## Cross-Platform SSH Handling

The container mounts the host's `~/.ssh` directory read-only. `ansible-run.sh` handles
platform-specific issues:

| Platform | Issue | Fix |
|----------|-------|-----|
| Windows (NTFS) | 0777 permissions on mounted files | Copy to `/tmp/.ssh`, chmod 600 |
| Linux | Files owned by host UID, not root | `HOME=/tmp` so SSH uses the copy |
| macOS | `UseKeychain` in SSH config | `sed` strips unsupported options |

## Acceptance Criteria

- [x] Ansible Docker image builds successfully
- [x] Project structure with inventory, vault, templates
- [x] `deploy.sh` starts container and runs playbooks via `docker compose exec`
- [x] SSH works from Windows, Linux, and macOS (macOS fix untested — see [T-06-8](T-06-8-macos-ssh-fix.md))
- [x] Ansible Vault for secret management (`edit-vault.sh`)
- [x] README documents SSH prerequisites, vault setup, and usage

# Branches

- `feature/T-06-2-ansible-setup`
