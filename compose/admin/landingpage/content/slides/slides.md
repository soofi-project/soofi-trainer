
<div style="display:flex; align-items:center; justify-content:center; width:100%; gap:20px;">
  <div style="padding-left: 30px;">
    <img src="media/logo.png" style="width:280px; margin-bottom:16px;" />
    <p>Sovereign Open Source Foundational Models</p>
  </div>
  <img src="media/soofi-partner-2.png" style="max-width:50%; max-height:500px; object-fit:contain; padding-right: 30px;" />
</div>

--

## Tools & more

- [Soofi UI](https://${LANDING_PAGE_HOSTNAME}:${SOOFI_UI_PORT})
- [Portainer](https://${LANDING_PAGE_HOSTNAME}:${PORTAINER_PORT})
- [MinIO Console](https://${LANDING_PAGE_HOSTNAME}:${MINIO_CONSOLE_PORT}/browser/knowledge) (${MINIO_ACCESS_KEY} | ${MINIO_SECRET_KEY})
- MCP Inspector
  - [Vector](https://${LANDING_PAGE_HOSTNAME}:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://vector-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345)
  - [Training Gateway](https://${LANDING_PAGE_HOSTNAME}:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://training-gateway:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345)
  - [EDC](https://${LANDING_PAGE_HOSTNAME}:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http:/edc-consumer-mcp:8081/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345)
  - [Huggingface](https://${LANDING_PAGE_HOSTNAME}:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://huggingface-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345)

--

## AAS & EDC

- [EDC Portal - Provider](https://${LANDING_PAGE_HOSTNAME}:${EDC_PORTAL_PROVIDER_PORT})
- [EDC Portal - Consumer](https://${LANDING_PAGE_HOSTNAME}:${EDC_PORTAL_CONSUMER_PORT})
- [AAS Web UI](https://${LANDING_PAGE_HOSTNAME}:${AAS_WEBUI_PORT})
- [Mnestix](https://${LANDING_PAGE_HOSTNAME}:${MNESTIX_BROWSER_PORT})


---

## Goals
- An open and scalable model ensemble
  - **Soofi 8B Dense** (Base, Instruct, Think) 
  - **Soofi 30B MoE, A3B** (Base, Instruct, Think)
  - **Soofi 120B MoE, A10B** (Base, Instruct, Think)
- Systemically integrated and learning agents
- Adaptability to industrial use cases

---


<!-- .slide: data-background-color="#0f1115" data-background-iframe="https://${LANDING_PAGE_HOSTNAME}:${SOOFI_UI_PORT}" data-background-interactive data-preload -->

---

<!-- .slide: data-background-color="#0f1115" data-background-iframe="https://${LANDING_PAGE_HOSTNAME}:${GRAFANA_PORT}/d/vllm-master-v2-mod/vllm-monitoring-modified?orgId=1&from=now-15m&to=now&timezone=browser&refresh=5s&theme=light" data-background-interactive -->

---

## Embedded Image

Path must be relative to `index.html`, not `slides.md`.

---
