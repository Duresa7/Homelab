# Compose Fleet Refresh

**Created:** 2026-09-04  
**Last updated:** 2026-09-04

**Implementation date:** 2026-09-04  
**Status:** Complete  
**Affected systems:** `docker-main`, `docker-blue`, `docker-network`, `media-01`, `alpha-prod-01`, `monitor-01`, `security-01`, `game-01`, `app-01`

## Outcome

I inventoried Docker on all 18 SSH Manager targets and found 43 active Compose projects with 66 running Compose containers on nine hosts. `ubuntu-dev` has Docker installed but no containers or Compose projects. The other eight configured targets do not have Docker installed.

I refreshed the 41 non-Coolify projects and their 61 already-running services. Each project passed `docker compose config --quiet`; registry-backed services completed `docker compose pull --ignore-buildable`; build-backed services completed `docker compose build --pull`; and `docker compose up -d` reconciled the existing service set. I named the running services explicitly so the pass did not start optional profiles or intentionally stopped workloads.

The two Coolify-owned projects were excluded after the scope clarification. An earlier pull and `up -d` check against those projects changed neither their image IDs nor their containers. I updated the `app-01` operating system instead.

## Changes

- NetBird management moved from 0.77.1 to 0.78.0 and the dashboard moved from 2.91.1 to 2.92.0.
- Grafana moved from 13.2.0 to 13.2.1. The local alert bot image was rebuilt from its existing source and base, and both containers were recreated.
- The Media Stack pulled every active service serially after LinuxServer's registry throttled the first parallel attempt. Gluetun, Prowlarr 2.5.2.5491-ls158, and qBittorrent 5.2.3_v2.0.14-ls474 were recreated. qBittorrent's recreation followed Gluetun because it shares Gluetun's network namespace.
- The TeamSpeak monitor and Wazuh MCP images were rebuilt with their current base images. Both services returned healthy with restart count 0.
- Pelican's retired `ghcr.io/pelican-dev/panel:latest` path returned `denied`. Pelican's [current Docker guide](https://pelican.dev/docs/panel/advanced/docker/) uses `ghcr.io/pelican/panel:latest`, and the [beta38 release](https://github.com/pelican/panel/releases/tag/v1.0.0-beta38) records the organization rename. I changed the live and versioned Compose reference to that path and moved the panel from beta36 to beta38. Wings beta27 remains the current Wings release and satisfies the documented 1.x compatibility line.
- On `app-01`, APT installed 28 ordinary upgrades. Docker Engine moved from 29.7.2 to 29.8.0, containerd to 2.3.4, Buildx to 0.37.0, and Docker Compose to 5.5.1. No reboot is required. `linux-image-amd64` remained outside the ordinary-upgrade transaction, and the held Wazuh agent remained held.

## Failed Attempts and Recovery

Protected `.env` files initially rejected unprivileged Compose reads for three projects. I reran those projects through SSH Manager's configured sudo path without changing ownership or permissions.

LinuxServer's registry throttled Prowlarr during the first Media Stack pull. I reran the eight service pulls serially; all eight succeeded, followed by a successful `up -d --pull never` reconciliation.

The first Pelican pull used the deployed service name from the container rather than the Compose service name and returned `no such service: pelican`. The corrected service is `panel`. That pull then exposed the retired image path, which I replaced with the current official path before the successful pull and recreation.

The Docker MCP Gateway project contains a local SSH Manager image. Its combined pull returned nonzero for that local image even with `--ignore-buildable`. I rebuilt the local service with `build --pull`, pulled the two registry-backed gateway services explicitly, and reconciled all three. Their image IDs were unchanged, so the control plane did not restart.

## Verification

- All 66 Compose containers were running after the pass. None was unhealthy or restarting, and every container reported restart count 0.
- NetBird's dashboard, embedded identity provider, and HTTPS entry point returned HTTP 200.
- All eight Media Stack services ran. Jellyfin and Gluetun were healthy; the Jellyfin, Seerr, Sonarr, Radarr, and Prowlarr checks passed; qBittorrent returned its expected unauthenticated HTTP 401; the VPN egress probe passed without printing the WAN address; and qBittorrent still used Gluetun's exact container namespace.
- Prometheus was ready with 56 of 56 active targets up. Grafana reported database `ok` at 13.2.1, and the alert bot was healthy with restart count 0.
- Wazuh MCP reported the Manager, Indexer, and MCP service healthy. A real `get_wazuh_running_agents` call through Executor completed after the rebuild.
- Pelican reported 1.0.0-beta38 on Laravel 13.25.0, healthy with restart count 0. Its local and HTTPS routes returned the expected 302. Wings stayed active at beta27, and the live and versioned Compose files had matching SHA-256 checksums.
- The SSH Manager gateway continued accepting remote calls, and Executor continued executing integration calls after their own Compose projects were reconciled.
- After APT restarted Docker on `app-01`, Coolify, Postgres, Redis, Realtime, Traefik, and cAdvisor all returned healthy with restart count 0. The local dashboard returned 302 and the unmatched proxy route returned 404. A final APT simulation reported zero ordinary upgrades remaining.

I created temporary LXC 123 snapshot `pre-pelican-beta38-20260904` before the Pelican database migration and removed it after the application, Wings, and HTTP checks passed. I retained no snapshot, backup, or standalone evidence folder. The observations above came from live SSH Manager and Executor checks during the maintenance window.

## Open State

The two packages held back on `app-01` were not part of the ordinary APT upgrade. Installing the kernel metapackage may require a reboot, and the Wazuh agent remains under its existing hold policy. No Compose deployment step remains open.
