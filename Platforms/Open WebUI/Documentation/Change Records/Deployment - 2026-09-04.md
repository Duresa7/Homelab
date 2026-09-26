# Open WebUI Deployment

**Created:** 2026-09-04  
**Last updated:** 2026-09-25
**Status:** Deployed; internal HTTPS completed on 2026-09-05 in [Open WebUI Internal HTTPS](../../../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Open%20WebUI%20Internal%20HTTPS%20-%202026-09-05.md)

## Summary

I added Open WebUI to the existing Ollama Compose project on `docker-main`. It tracks the rolling `main` tag and currently reports version 0.11.3. The frontend is healthy at `http://192.168.40.35:3002`, keeps authentication enabled, persists its state in a named volume, and discovers `llama3.1:8b` through the private Compose network. I did not recreate or restart Ollama.

## Baseline

TCP/3002 was free. The LXC had 13 GiB memory available and 61 GiB free on its root filesystem. Ollama was healthy with restart count zero, and the host ran 14 containers before this change.

## Implementation

I initially selected 0.11.1 from a stale search result. A direct read of the official GitHub latest-release API showed that 0.11.3, published on 2026-08-31, was current. I corrected the deployment before handoff and pinned `ghcr.io/open-webui/open-webui:v0.11.3` to registry digest `sha256:d428020d5f091491cf1ef6a186a7fd080f388bfbf2c2c221b78a3b1bead0d591`. The image carries a built-in health check against `/health`.

I then changed the image to `ghcr.io/open-webui/open-webui:main`, removed the immutable digest pin, and set `pull_policy: always`. Open WebUI officially documents `main` and `latest` as identical rolling tags. On 2026-09-04, `main` resolved to registry digest `sha256:33e61767ff4254af89a1ed59483f286d33be00a3ed282248d43c263fa667d7fa`, image ID `sha256:f87fa53a5b7c1540b53e0472948b071853baf908d508391258e5bdc7be9ba5ed`, and application version 0.11.3. This intentionally trades immutable deployment reproduction for automatic tracking on future pulls and recreates.

I added `open-webui` to `/opt/docker/ollama/docker-compose.yml` and the matching versioned file. It depends on healthy Ollama, uses `OLLAMA_BASE_URL=http://ollama:11434`, enables authentication, binds only to `192.168.40.35:3002`, and mounts `ollama_open-webui-data` at `/app/backend/data`. I generated a persistent signing key in the untracked `/opt/docker/ollama/.env` file at mode `0600`.

I ran `docker compose up -d --no-deps open-webui`. Ollama had the same full container ID and restart count zero before and after the deployment.

## Network Publication

I added TCP/3002 to UniFi policy `Allow NPM to docker-main web UIs`. The policy still permits only NPM at `192.168.85.2` to the listed ports on `192.168.40.35`. A request from `docker-network` to the Open WebUI health endpoint succeeded after the change.

I created local A record `openwebui.alphasecunited.com` at `192.168.85.2` with a 300-second TTL. The NPM proxy host is not yet present. The stored NPM administrator credential does not match the one active in the application, and I did not reset that shared credential without separate approval. The direct internal URL remains the working access path.

## Verification

- `open-webui` reached healthy with zero restarts.
- The Compose service uses `ghcr.io/open-webui/open-webui:main` with `pull_policy: always`.
- The running image matched the registry digest observed for `main` during deployment.
- Open WebUI's `/api/version` endpoint returned `0.11.3` after the recreate.
- The recreate retained the existing `ollama_open-webui-data` volume.
- `GET /health` returned `{"status":true}`.
- A request from inside `open-webui` to `http://ollama:11434/api/tags` returned `llama3.1:8b`.
- The browser rendered the welcome page and initial administrator-account form.
- Cloudflare's public resolver returned NXDOMAIN for `openwebui.alphasecunited.com`.
- Ollama remained healthy with the same container ID and restart count zero.
- All 15 containers on `docker-main` were running after deployment.
- The root filesystem retained 55 GiB free after caching the 5.1 GB image.

## Recovery

I can stop and remove only the `open-webui` service without touching Ollama. I leave `ollama_open-webui-data` in place unless I deliberately intend to delete the frontend accounts, chats, and settings. If I abandon HTTPS publication, I also remove the staged local DNS record and TCP/3002 from the NPM-to-`docker-main` firewall policy.
