# Open WebUI

**Created:** 2026-09-04  
**Last updated:** 2026-09-04

I run Open WebUI as the authenticated browser frontend for the Ollama deployment on `docker-main`. It shares the Ollama Compose network, reaches the API by the service name `ollama`, and does not receive direct GPU access. Ollama remains the only component that runs inference on the GTX 1080 Ti.

## Current State

| Item | Current value |
| --- | --- |
| Status | Healthy; initial administrator form rendered; Ollama model discovery verified |
| Host | Galaxy LXC 110 `docker-main` |
| Live project | `/opt/docker/ollama` |
| Version | Rolling `main` tag; application currently reports Open WebUI 0.11.3 |
| Image | `ghcr.io/open-webui/open-webui:main` with `pull_policy: always`; observed registry digest `sha256:33e61767ff4254af89a1ed59483f286d33be00a3ed282248d43c263fa667d7fa` on 2026-09-04 |
| Direct URL | `http://192.168.40.35:3002` |
| Authentication | Enabled; the first registered account becomes the administrator and closes initial signup |
| Ollama connection | `http://ollama:11434` over the private Compose network |
| Persistent state | Named volume `ollama_open-webui-data` mounted at `/app/backend/data` |
| Session key | Generated locally, mode `0600`, and held outside this repository in `/opt/docker/ollama/.env` |
| WAN exposure | None |

UniFi has the local `openwebui.alphasecunited.com` A record and the narrow NPM-to-`docker-main` TCP/3002 firewall path. The NPM administrator credential was repaired on 2026-09-04 and now authenticates, so the blocker on the proxy host is cleared. Adding the proxy host itself is still outstanding, and until it exists I use the direct internal URL above.

## Records

- [Shared Compose configuration](../Ollama/Configuration/docker-compose.yml)
- [Environment template](../Ollama/Configuration/.env.example)
- [Operations runbook](Documentation/Runbook.md)
- [Deployment record](Documentation/Change%20Records/Open%20WebUI%20Deployment%20-%202026-09-04.md)
- [Ollama platform](../Ollama/README.md)
