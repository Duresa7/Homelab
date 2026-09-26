# Open WebUI

**Created:** 2026-09-04  
**Last updated:** 2026-09-25

I run Open WebUI as the authenticated browser frontend for the Ollama deployment on `docker-main`. It shares the Ollama Compose network, reaches the API by the service name `ollama`, and does not receive direct GPU access. Ollama remains the only component that runs inference on the GTX 1080 Ti.

## Current State

| Item | Current value |
| --- | --- |
| Status | Healthy; internal HTTPS, initial administrator form, and Ollama model discovery verified |
| Host | Galaxy LXC 110 `docker-main` |
| Live project | `/opt/docker/ollama` |
| Version | Rolling `main` tag; `/api/version` returned 0.11.4 on 2026-09-24 |
| Image | `ghcr.io/open-webui/open-webui:main` with `pull_policy: always`; observed registry digest `sha256:1a6399d237dc392a2313e0ca826020b3fd5d22536357840eb63393d18dc8b924` on 2026-09-13 |
| Primary URL | `https://openwebui.alphasecunited.com` |
| Direct recovery URL | `http://192.168.40.35:3002` |
| Authentication | Enabled; the first registered account becomes the administrator and closes initial signup |
| Ollama connection | `http://ollama:11434` over the private Compose network |
| Persistent state | Named volume `ollama_open-webui-data` mounted at `/app/backend/data` |
| Session key | Generated locally, mode `0600`, in `/opt/docker/ollama/.env` |
| WAN exposure | None |

UniFi resolves `openwebui.alphasecunited.com` to NPM and permits only NPM to reach `docker-main` on TCP/3002. NPM proxy host 28 forwards the name to that backend with the shared wildcard certificate, Force SSL, HTTP/2, WebSockets, and Block Common Exploits enabled. The name remains internal: Cloudflare public DNS returns NXDOMAIN and no WAN rule publishes it.

## Records

- [Shared Compose configuration](../Ollama/Configuration/docker-compose.yml)
- [Environment template](../Ollama/Configuration/.env.example)
- [Operations runbook](Documentation/Runbook.md)
- [Deployment record](Documentation/Change%20Records/Deployment%20-%202026-09-04.md)
- [Internal HTTPS record](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Open%20WebUI%20Internal%20HTTPS%20-%202026-09-05.md)
- [Ollama platform](../Ollama/README.md)

On 2026-09-13 I refreshed the rolling image and it still reported 0.11.3; direct and HTTPS health checks and Ollama model discovery passed ([maintenance record](../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-13.md)). It reported 0.11.4 by 2026-09-24.
