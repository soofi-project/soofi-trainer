
![Logo](media/logo.png)

Sovereign Open Source Foundational Models

--

## Tools and more

- [Soofi UI](http://${LANDING_PAGE_HOSTNAME}:${SOOFI_UI_PORT})
- [Portainer](http://${LANDING_PAGE_HOSTNAME}:${PORTAINER_PORT})
- [Open-WebUI](http://${LANDING_PAGE_HOSTNAME}:${OPENWEBUI_PORT})
- [n8n](http://${LANDING_PAGE_HOSTNAME}:${N8N_EXTERNAL_PORT}) (${N8N_BASIC_AUTH_USER} | ${N8N_BASIC_AUTH_PASSWORD})
- [MinIO Console](http://${LANDING_PAGE_HOSTNAME}:${MINIO_CONSOLE_PORT}/browser/knowledge) (${MINIO_ACCESS_KEY} | ${MINIO_SECRET_KEY})
- MCP Inspector
  - [Vector](http://${LANDING_PAGE_HOSTNAME}:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://vector-mcp:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345)
  - [Training Gateway](http://${LANDING_PAGE_HOSTNAME}:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://training-gateway:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345)
  - [EDC](http://${LANDING_PAGE_HOSTNAME}:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://training-gateway:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345)
  - [Huggingface](http://${LANDING_PAGE_HOSTNAME}:${MCPINSPECTOR_CLIENT_PORT}/?transport=streamable-http&serverUrl=http://training-gateway:8000/mcp/&MCP_PROXY_AUTH_TOKEN=dev-stack-token-12345)

---

<iframe
  src="http://${LANDING_PAGE_HOSTNAME}:${SOOFI_UI_PORT}"
  style="width:95vw; height:95vh; border:none;"
  allow="microphone">
</iframe>

---

<iframe
  src="http://${LANDING_PAGE_HOSTNAME}:${GRAFANA_PORT}/d/vllm-master-v2-mod/vllm-monitoring-modified?orgId=1&from=now-15m&to=now&timezone=browser&refresh=5s&theme=light"
  style="width:95vw; height:95vh; border:none;">
</iframe>

---

## Embedded Image

Path must be relative to `index.html`, not `slides.md`.

---
