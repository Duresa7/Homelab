# Step 3 Agent Deployment and Verification

**Created:** 2026-07-28  
**Last updated:** 2026-08-04

**Capture date:** 2026-07-28  
**Execution mechanism:** SSH Manager MCP, remote POSIX shell  
**Targets:** `docker_network`, `blue_server` CT 108, `red_server` CT 842

## Deployment

I installed [the versioned compose file](../../../Configuration/portainer-edge-agent/docker-compose.yml) under `/opt/docker/portainer-edge-agent/docker-compose.yml` on all three targets. Each host-specific `.env` was generated from `<REDACTED_PASSWORD_MANAGER>`, transferred through a mode-0600 staging file, installed as `root:root` mode 0600, & removed from the staging location.

The secret-bearing transfer transcript isn't retained because the file content contains the Edge ID & key. The retained post-install command inspects only file metadata:

```sh
cd /opt/docker/portainer-edge-agent
stat -c '%n|%a|%U|%G' docker-compose.yml .env
docker compose config --quiet
docker compose up -d
```

## File and Container Results

| Target | Compose mode | `.env` mode | Compose validation | Agent state |
|---|---:|---:|---:|---|
| `media-01` | 0644 | 0600 | Exit 0 | Running |
| `docker-network` | 0644 | 0600 | Exit 0 | Running |
| `docker-blue` | 0644 | 0600 | Exit 0 | Created; task startup failed |

Both running agents report image `portainer/agent:2.39.1` & restart policy `always`. Their environment-variable names are `EDGE`, `EDGE_ID`, `EDGE_INSECURE_POLL`, `EDGE_KEY`, & `PATH`.

## Existing Workloads

After deployment:

```text
docker-network: cadvisor, netbird-server, netbird-dashboard, nginx-proxy-manager, portainer_edge_agent
media-01: radarr, prowlarr, jellyseerr, cadvisor, qbittorrent, jellyfin, gluetun, sonarr, flaresolverr, portainer_edge_agent
docker-blue: cadvisor, hbbs, hbbr
```

No existing container reported restarting or unhealthy.

## Portainer Verification

```http
GET /api/endpoints
GET /api/endpoints/8/docker/containers/json?all=1
GET /api/endpoints/9/docker/containers/json?all=1
```

| Name | Check-in observed | Tunnel API | Container count |
|---|---|---|---:|
| `media-01` | Yes | Reachable | 10 |
| `docker-network` | Yes | Timed out | Not returned |
| `docker-blue` | No | Unavailable | Not returned |

The `docker-network` result separates polling from management: TCP 9443 accepts the check-in, while blocked TCP 8000 prevents the reverse tunnel.
