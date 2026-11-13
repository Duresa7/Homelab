# Container Image Updates

**Created:** 2026-11-12  
**Last updated:** 2026-11-12

## Scope

At 10:40 PM Eastern I pulled the image reference of every running container on the seven Docker hosts that run Compose workloads: `docker-main`, `docker-blue`, `docker-network`, `media-01`, `monitor-01`, `alpha-prod-01` and `security-01`. For each container I compared the image ID the reference now resolved to with the image ID it was running. A match only proves the configured reference is current; a pinned tag or digest that matches does not show the application is on its newest release. `app-01` is stopped and `e2b-01` was out of scope.

## Pull result

| Host | Newer image available | Already current |
|---|---|---|
| docker-main | `immich-server:release`, `immich-machine-learning:release-cuda`, `eceasy/cli-proxy-api:latest`, `pgvector/pgvector:pg18` (BookOrbit DB), `postgres:16` (Sure DB) | App Portal 0.6.0, BookOrbit app (digest-pinned), Dockhand v1.0.51, Forgejo 16, Immich Postgres and Valkey (digest-pinned), Ollama 0.35.1, Open WebUI `main`, Sure 0.7.5-hotfix.1, Sure Redis, cAdvisor |
| docker-blue | Hawser | Docker MCP Gateway v0.43.3, Executor 2.0.0-beta.41, MeshCentral, RustDesk `hbbs` and `hbbr`, cAdvisor |
| docker-network | Hawser, NetBird server and dashboard | Nginx Proxy Manager 2.15.1, cAdvisor |
| media-01 | Hawser, qBittorrent, Radarr, Sonarr, Prowlarr, Seerr | Jellyfin, Gluetun, FlareSolverr, cAdvisor |
| monitor-01 | Hawser | Grafana, Prometheus, blackbox exporter, PVE exporter, NUT exporter, PeaNUT, cAdvisor |
| alpha-prod-01 | Hawser, Minecraft (`stable-java25`), Playit agent, TeamSpeak 02 and 03 | TS3 Manager, cAdvisor |
| security-01 | Hawser | cAdvisor |

Five pulls failed:

- `alert-bot`, `wazuh-mcp-server`, `unifi-network-mcp` and `teamspeak-monitor` under `forgejo.alphasecunited.com/homelab-images` returned `unauthorized`. These hosts hold no login for the Forgejo registry, which is the likely cause of the five private-registry failures the [2026-10-28 check](Compose%20Update%20Check%20-%202026-10-28.md) left undiagnosed.
- `homelab/ssh-mcp:2.22.0` on `docker-blue` is a locally built image with no registry behind it, so `pull access denied` is expected.

The deliberate holds (Nginx Proxy Manager 2.15.1, Docker MCP Gateway v0.43.3 and App Portal 0.6.0) had nothing newer at their pinned references and were not touched.

## Recreated

Starting at 11:02 PM Eastern, I recreated only the services with a newer image, project by project, with `docker compose up -d --no-deps --pull never <services>` from each project's own working directory and Compose files. Every project returned exit code 0. Services without a newer image, and every dependency of a recreated service, kept running.

| Host | Project | Services |
|---|---|---|
| docker-main | `immich` | `immich-server`, `immich-machine-learning` |
| docker-main | `cli-proxy-api` | `cli-proxy-api` |
| docker-main | `bookorbit` | `postgres` |
| docker-main | `sure` | `db` |
| media-01 | `media-stack` | `qbittorrent`, `radarr`, `sonarr`, `prowlarr`, `jellyseerr` |
| alpha-prod-01 | `minecraft`, `playit-agent`, `teamspeak-02`, `teamspeak-03` | one service each |
| all six other than docker-main | `hawser` | `hawser` |

NetBird's newer images were not deployed: I retired NetBird the same evening ([retirement record](../../Archive/Platforms/Netbird/Documentation/Change%20Records/Retirement%20-%202026-11-12.md)).

## Verification

About five minutes after the recreates:

- docker-main: `immich_server`, `immich_machine_learning`, `sure-db` and `bookorbit-db` reported `healthy`, and `cli-proxy-api` was up. `immich_server` reported image version v3.4.1 and logged `Finished running migrations`; `GET /api/server/ping` returned 200. `sure-web`, `sure-worker` and `bookorbit-app` kept running against their recreated databases.
- media-01: Sonarr, Radarr and Prowlarr answered 302, Seerr 307 and the qBittorrent WebUI 401 on loopback, which is each application's usual unauthenticated response. Gluetun stayed healthy and was not recreated.
- alpha-prod-01: Minecraft reported `healthy` and logged `Done (0.228s)!`; the Playit agent logged `playit connected; tunnels loaded` with three tunnels; both TeamSpeak servers were up.
- Hawser reported `healthy` on all six hosts.

No transcript is retained; this record holds what each check returned. I created no snapshot or backup.

## Open items

- Give the Docker hosts a read-only login for the Forgejo registry, or move the four private images to a reference those hosts can pull, so the update check covers them.
- Version-pinned and digest-pinned applications still need a release-notes check; this pass only proves their configured references are current.
