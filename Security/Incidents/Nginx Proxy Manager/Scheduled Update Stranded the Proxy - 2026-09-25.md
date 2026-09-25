# Scheduled Update Stranded the Proxy - 2026-09-25

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

## Incident Metadata

| Field | Value |
|-------|-------|
| Incident date | 2026-09-25 |
| Report timezone | America/New_York (EDT) |
| Service | Nginx Proxy Manager on CT 107 `docker-network` (`192.168.85.2`) |
| Trigger | Dockhand's daily 3:00 AM auto-update on the `docker-network` environment |
| Duration | About 3 hours 12 minutes, 3:00:28 AM to 6:12:39 AM, plus about 10 seconds during the corrective recreate at 6:15 AM |
| Status | Resolved |
| Severity | SEV-2 - Service Outage |

## Summary

Dockhand's scheduled update pulled a new `jc21/nginx-proxy-manager:latest` image (NPM 2.16.0, built 2026-09-24) and stopped the running 2.15.1 container so it could recreate it. Dockhand drives `docker-network` through its Hawser Edge agent, and every Hawser agent reaches Dockhand at `wss://dockhand.alphasecunited.com`, which is an NPM proxy host. Stopping NPM cut the connection that was carrying the update, so the recreate step never ran. The container exited with code 0, and `unless-stopped` does not restart a container that was stopped on request, so NPM stayed down until I started it by hand.

The image still waiting to be applied meant the same sequence would have run again at 3:00 AM on 2026-09-26.

## Impact

| Area | Impact |
|------|--------|
| Internal HTTPS | Every name behind `192.168.85.2` refused TCP 80, 81 and 443: NetBird and the 23 internal application hosts in the [proxy-host inventory](../../../Platforms/Nginx%20Proxy%20Manager/Configuration/internal-proxy-hosts.md) |
| Executor | `mcp.alphasecunited.com` was unreachable, so my agent clients had no SSH Manager, UniFi, Wazuh or Cloudflare MCP. That is how I found the outage: the client reported `ECONNREFUSED` on the Executor endpoint |
| Dockhand | All six Hawser agents lost their connection to Dockhand and retried every minute or so |
| Backends | Unaffected. Executor still answered on `192.168.40.39:4788` and the gateways on 8811 and 8812 |
| Data | None lost. The container stopped cleanly and was never recreated, so `data/` and `letsencrypt/` were untouched |

## Timeline (EDT)

| Time | Event |
|------|-------|
| 3:00:00 AM | Hawser on `docker-network` receives Dockhand's container and image inspection calls |
| 3:00:01 AM | `POST /images/create?fromImage=jc21/nginx-proxy-manager&tag=latest` |
| 3:00:28 AM | `POST /containers/ae2e5674.../stop` for `nginx-proxy-manager`. In the same second Hawser logs `Read error: websocket: close 1006 (abnormal closure): unexpected EOF` |
| 3:00:29 AM | NPM logs `PID 302 received SIGTERM` then `Stopping.`; Hawser's first reconnect fails with `dial tcp 192.168.85.2:443: connect: connection refused` |
| 3:00:32 AM | The stop returns 204; the container is `Exited (0)`. No create or start call follows |
| 6:07 AM | I found NPM exited during diagnosis; ports 80, 81 and 443 refused while ping and SSH answered |
| 6:12:39 AM | `docker start nginx-proxy-manager`; healthy on the unchanged 2.15.1 image |
| 6:13:36 AM | Hawser logs `Connected to Dockhand server` |
| 6:15 AM | Recreated with the pinned image and the update-exclusion label; Hawser's reconnects fail at 6:15:14 and 6:15:16 |
| 6:15:21 AM | Hawser logs `Connected to Dockhand server` |
| 6:15:37 AM | NPM reports healthy; the full host sweep follows and passes |

## Root Cause

Dockhand updates a container by stopping it and then creating its replacement, and it issues both steps over the Hawser connection. NPM is on that connection's path. Upstream's [manual](https://dockhand.pro/manual/) names this failure for socket proxies: a container Dockhand depends on to reach Docker must carry `dockhand.update=false`, because updating it disconnects Dockhand partway through. I had applied that label to the Hawser containers on 2026-09-15 but not to NPM, and NPM tracked `latest`, so the first NPM release after the 2026-09-18 schedule verification triggered it.

## Corrective Action

1. Started the stopped container on its existing image (`sha256:52b2c599...`, NPM 2.15.1).
2. Copied `/opt/docker/nginx-proxy-manager/docker-compose.yml` before editing it. The copy held no secrets and matched the tracked reference byte for byte; it is at [Backups/docker-network-nginx-proxy-manager-docker-compose-2026-09-25.yml](../../../Backups/docker-network-nginx-proxy-manager-docker-compose-2026-09-25.yml) and I deleted it from the host.
3. Pinned the image to `jc21/nginx-proxy-manager:2.15.1` and added the label `dockhand.update: "false"`. I pulled the `2.15.1` tag first and confirmed it resolves to the same image ID that was running, so the recreate changed no NPM version. I did not take 2.16.0 during the repair; it is a minor release and gets its own planned upgrade.
4. Applied the same image and label to Dockhand's imported definition at `/opt/docker/dockhand/stacks/imported/docker_network/nginx-proxy-manager/compose.yaml` on `docker-main`, so a Dockhand deployment of the stack cannot undo the fix. The file stayed root-owned at mode 0600 and `docker compose config -q` passed.
5. Updated the tracked [Compose reference](../../../Platforms/Nginx%20Proxy%20Manager/Configuration/docker-compose.yml).

## Validation

On `docker-network` after the recreate:

```text
status=running health=healthy image=sha256:52b2c59994f3d36acfcf70a1626f29734df0ed8c71bacc0269f78b6f939858bb ip=172.31.85.10 restart=unless-stopped label=false
admin_http=200
netbird_https=200
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

From `ubuntu-dev`, every live host in the proxy inventory returned 200 or an application redirect with a valid certificate. Two exceptions predate the incident and are not NPM faults. `appportal` returns 404 at `/`, and so does its backend at `192.168.40.35:3004` directly, because it serves an API. `dashboard` returns 502 because Homelab Dashboard on `docker-main` has been stopped since 2026-09-22, as [Services.md](../../../Operations/Inventory/Galaxy/Services.md) records. `games` and `wings` do not resolve; I retired them on 2026-09-12.

The other five Hawser hosts (`docker-blue`, `monitor-01`, `media-01`, `alpha-prod-01`, `security-01`) had no stopped application container, so no other update was cut off mid-run. Executor reconnected to my agent session once NPM was back.

## Open

- NPM no longer auto-updates. The 2.16.0 image is on the host, tagged `latest` and unused, for a planned upgrade that I run by hand while the Hawser connection is not needed.
- I have not observed a scheduled 3:00 AM run with the label in place. The first one is 2026-09-26.
