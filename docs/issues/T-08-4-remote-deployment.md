# Task

- user story: #US-08
- depends on: #T-08-2, #T-06-2

/label ~UserStory_US-08
/label ~Task
/label ~ToDo

# Description

**Remote Container Orchestration**

Deploy and manage training containers on remote infrastructure (Docker Compose or Kubernetes). The Training Gateway triggers container starts on the remote side and receives webhook callbacks.

## Deployment Options

### Option A: Remote Docker Compose

For single-server setups (e.g. the H200 lab server):

- Training Gateway uses Docker API (remote TCP or SSH tunnel) to start containers
- Containers run as one-shot jobs (`docker run --rm`)
- Gateway manages container lifecycle (start, monitor, stop)
- Reuses Ansible patterns from US-06 for server provisioning

### Option B: Kubernetes

For multi-node or cloud environments:

- Training Gateway submits Kubernetes Jobs
- Each training job creates a Pod with the appropriate pipeline image
- K8s handles scheduling, resource allocation, GPU assignment
- Gateway watches Job status via K8s API

## Network Configuration

```
Soofi Trainer Stack              Remote Infrastructure
(e.g. dev machine)               (e.g. H200 server)
+-------------------+            +------------------------+
| Training Gateway  |---REST---->| Docker API / K8s API   |
|   :8200           |            |                        |
|                   |<--Webhook--| Training Container     |
| /webhooks/*       |            | (calls back on events) |
+-------------------+            +------------------------+
```

- Gateway needs outbound access to remote Docker/K8s API
- Training containers need outbound access to gateway webhook URL
- Firewall rules / SSH tunnels as required

## Ansible Playbooks

Following the same Ansible patterns as US-06:

| Playbook | Purpose |
|----------|---------|
| `setup-docker-training.yml` | Configure Docker for training jobs (pull images, network setup) |
| `setup-k8s-training.yml` | Configure Kubernetes namespace, RBAC, GPU resource quotas |
| `deploy-training-images.yml` | Pull/build training pipeline images on remote |

## Resource Management

- GPU memory allocation per training job (environment variables)
- Coexistence with inference models (US-06) on the same GPU server
- One training job at a time in Phase 1 (queue in gateway)
- Container resource limits (CPU, memory, GPU)

## Configuration

Environment variables in `.env`:

| Variable | Description | Example |
|----------|-------------|---------|
| `TRAINING_BACKEND` | `docker` or `kubernetes` | `docker` |
| `TRAINING_DOCKER_HOST` | Remote Docker API URL | `ssh://user@gpu-server` |
| `TRAINING_K8S_NAMESPACE` | Kubernetes namespace | `soofi-training` |
| `TRAINING_GPU_DEVICE` | GPU device ID for training | `0` |
| `TRAINING_GATEWAY_URL` | Callback URL for containers | `http://gateway:8200` |

## Acceptance Criteria

- [ ] Training containers start on remote Docker host via gateway
- [ ] Alternative: Training containers start as Kubernetes Jobs via gateway
- [ ] Ansible playbooks provision the remote infrastructure for training
- [ ] Playbooks follow existing US-06 Ansible patterns
- [ ] Network connectivity works between gateway and remote containers (both directions)
- [ ] GPU resources are allocated and limited per training job
- [ ] Training jobs coexist with inference models on the same server
- [ ] Configuration via `.env` allows switching between Docker and K8s backends
- [ ] Container images are available on the remote infrastructure

# Branches

- feature/T-08-4-remote-deployment
