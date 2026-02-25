# Task

- user story: [US-06](US-06-inference-server.md)
- blocks: [T-06-4](T-06-4-trainer-integration.md)

# Description

**Stack Cleanup: Remove LiteLLM, Open WebUI, and Kubernetes Scaffolding**

The inference server should do one thing: serve models. Triton's built-in OpenAI frontend (port 9000)
makes LiteLLM redundant. Open WebUI belongs in application stacks (Soofi Trainer already has one),
not on the dedicated GPU server. The `kubernetes/` directory is out-of-scope scaffolding.

Repository: [soofi-inference-server](https://mrk40.dfki.de/soofi/soofi-inference-server)

## Remove LiteLLM

LiteLLM was used to translate OpenAI API calls into Triton's KServe V2 format. Triton's own
OpenAI frontend (port 9000) does this natively — LiteLLM is no longer needed.

### `docker/docker-compose.yml`
- Remove the `litellm` service entirely
- Remove `docker/litellm-config.yaml`

### `ansible/templates/triton.env.j2`
- Remove `LITELLM_PORT` and `LITELLM_MASTER_KEY`

### `ansible/inventory/group_vars/gpu_nodes/vars.yaml`
- Remove `litellm_port`

### `ansible/inventory/group_vars/gpu_nodes/vault.yaml`
- Remove `litellm_master_key` from the vault:
  ```
  ./scripts/edit-vault.sh
  ```

### `ansible/playbooks/triton_deploy.yaml`
- Remove the "Copy litellm-config.yaml" task

### `models/model_repository/mistral-7b-awq/`
- Remove the static example config — Ansible generates all model configs from templates
- `config.pbtxt` should be minimal: just `backend: "vllm"` + `instance_group [{kind: KIND_MODEL}]`
- All vLLM parameters belong in `model.json`, not in the `parameters` block of `config.pbtxt`

## Remove Open WebUI

The GPU server is dedicated inference hardware — a user-facing chat UI does not belong there.
Application stacks (Soofi Trainer, soofi-cluster) run their own Open WebUI instances and connect
to Triton via `OPENAI_API_BASE`. Running Open WebUI on the inference server wastes resources and
unnecessarily exposes a public port on lab hardware.

### `docker/docker-compose.yml`
- Remove the `open-webui` service and the `open-webui-data` volume

### `ansible/templates/triton.env.j2`
- Remove `WEBUI_PORT`, `WEBUI_AUTH`, `WEBUI_NAME`

### `ansible/inventory/group_vars/gpu_nodes/vars.yaml`
- Remove `webui_port`, `webui_auth`, `webui_name`

## Add `docker-compose.dev.yml` for Local Testing

To allow local end-to-end tests against a running Triton instance without needing a separate
application stack, provide a Compose override file that adds Open WebUI:

```bash
# Local test with UI
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up

# Production (Triton only)
docker compose -f docker/docker-compose.yml up
```

### `docker/docker-compose.dev.yml`
- Adds the `open-webui` service pointing to `http://triton:9000/v1`
- Joins the same `inference-net` network
- No additional secrets needed (no `LITELLM_MASTER_KEY`)

## Remove Kubernetes Scaffolding

The `kubernetes/` directory is out of scope (US-06 explicitly excludes K8s — it belongs in
`soofi-cluster`). The files are auto-generated, have correctness issues, and are misleadingly
incomplete:
- Outdated image tag (`24.08` vs current `26.01`)
- `storageClassName: local-path` requires Rancher's local-path-provisioner (not standard K8s)
- `initialDelaySeconds` too short for 72B model startup
- No OpenAI frontend (port 9000 missing), no `triton-start.sh` integration

### Changes
- Delete the entire `kubernetes/` directory
- Add a note to `README.md` that K8s deployment is managed via the
  [soofi-cluster](https://mrk40.dfki.de/soofi/soofi-cluster) project using NVIDIA's official
  Helm chart and GPU Operator

## Port Map After Cleanup

| Port | Service |
|------|---------|
| 8000 | Triton KServe V2 HTTP (internal, backwards compatibility) |
| 8001 | Triton gRPC |
| 8002 | Triton Metrics (Prometheus) |
| 9000 | Triton OpenAI-compatible API — the only external endpoint |

## Acceptance Criteria

- [ ] LiteLLM service and config removed
- [ ] Open WebUI service and volume removed
- [ ] `litellm_master_key` removed from vault
- [ ] `kubernetes/` directory deleted
- [ ] Static model example (`mistral-7b-awq/`) cleaned up or removed
- [ ] `docker-compose.yml` contains only the `triton` service
- [ ] `docker-compose.dev.yml` adds Open WebUI for local testing
- [ ] README updated: architecture diagram, port table, clean description
- [ ] Stack starts cleanly with `docker compose up`
- [ ] `curl localhost:9000/v1/models` returns model list (end-to-end verify)
- [ ] Dev stack (`docker compose -f ... -f docker-compose.dev.yml up`) shows Open WebUI on port 3000

# Branches

- `feature/T-06-7-cleanup`
