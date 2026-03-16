# Task

- user story: [US-09](US-09-agent-observability.md)
- depends on: [T-06-3](T-06-3-server-provisioning.md)

/label ~UserStory_US-09
/label ~Task
/label ~ToDo

# Description

**GPU Monitoring Dashboard (Prometheus + Grafana)**

Live GPU monitoring for the H200 inference server, embedded in the Soofi UI via Grafana.
Makes local inference tangible for demo audiences: "No cloud API — our model runs on this GPU,
and here's the proof."

## Architecture

```
Triton /metrics → Prometheus (scrape) → Grafana (dashboard) → iframe in Side Panel
```

## Docker Compose Services

### Prometheus

```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: prometheus
  restart: unless-stopped
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus-data:/prometheus
  networks:
    - soofi-network
```

`monitoring/prometheus.yml`:
```yaml
scrape_configs:
  - job_name: triton
    scrape_interval: 5s
    static_configs:
      - targets: ["${TRITON_HOST}:${TRITON_METRICS_PORT}"]
```

### Grafana

```yaml
grafana:
  image: grafana/grafana:latest
  container_name: grafana
  restart: unless-stopped
  ports:
    - "${GRAFANA_PORT}:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    - GF_AUTH_ANONYMOUS_ENABLED=true
    - GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
    - GF_SECURITY_ALLOW_EMBEDDING=true
  volumes:
    - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    - grafana-data:/var/lib/grafana
  depends_on:
    - prometheus
  networks:
    - soofi-network
```

Anonymous access enabled so the iframe works without login. Embedding allowed via
`GF_SECURITY_ALLOW_EMBEDDING`.

## Grafana Dashboard

A single "Soofi GPU Monitor" dashboard with panels:

| Panel | Metric | Visual |
|-------|--------|--------|
| GPU Utilization | `nv_gpu_utilization` | Gauge (0–100%) |
| Tokens/sec | `nv_inference_count` rate | Time series |
| GPU Memory | `nv_gpu_memory_used_bytes` / `nv_gpu_memory_total_bytes` | Gauge |
| Inference Latency | `nv_inference_request_duration_us` p95 | Time series |

Dashboard provisioned automatically via JSON file in `monitoring/grafana/provisioning/dashboards/`.

## UI Integration

Extend the `show_dashboard` tool in the Interaction Agent:

```python
elif name == "gpu_monitoring":
    surface = gpu_monitoring_surface()  # returns iframe URL to Grafana dashboard
```

The dashboard opens in the **side panel** (same as document viewer and agent cards).

Grafana panel URL with parameters for clean embedding:
```
http://grafana:3000/d/soofi-gpu/soofi-gpu-monitor?orgId=1&kiosk&theme=light
```

## .env Additions

```
GRAFANA_PORT=3003
GRAFANA_PASSWORD=soofi-demo
TRITON_HOST=triton-host
TRITON_METRICS_PORT=8002
```

## Example Interactions

- "Zeig mir die GPU-Auslastung"
- "Wie ausgelastet ist die H200?"
- "Zeig mir das GPU-Monitoring"

## Acceptance Criteria

- [ ] Prometheus scrapes Triton `/metrics` endpoint
- [ ] Grafana dashboard shows GPU Utilization, Tokens/sec, Memory, Latency
- [ ] Dashboard provisioned automatically (no manual setup after `docker compose up`)
- [ ] Grafana allows anonymous access and iframe embedding
- [ ] `show_dashboard("gpu_monitoring")` opens Grafana dashboard in side panel
- [ ] Dashboard visibly reacts when the agent generates a response (GPU utilization goes up)
- [ ] Services added to `docker-compose.yml` with appropriate dependencies
- [ ] `.env` variables for Grafana port, password, Triton host documented

# Branches

- feature/T-09-5-gpu-monitoring
