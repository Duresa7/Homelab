# NetBird

**Created:** 2026-07-11  
**Last updated:** 2026-09-25

NetBird is my self-hosted WireGuard mesh. The control plane runs on the `docker-network` LXC beside Nginx Proxy Manager, and the dashboard is published at `https://netbird.alphasecunited.com` through NPM. Peers reach only Access-A (VLAN 85) and get no DNS from NetBird. The other remote path into the lab is the UniFi `Management Access` WireGuard server; both are described in [Access Paths](../../Architecture/Access-Paths.md).

## Current State

Versions read back on 2026-09-24; routing and DNS read from the management store on 2026-09-04.

| Item | Current value |
|---|---|
| Compute | Galaxy CT 107 `docker-network`, `192.168.85.2/24`, VLAN 85 |
| Containers | `netbird-server` (`netbirdio/netbird-server:latest`, which logs "Starting combined NetBird server") and `netbird-dashboard` (`netbirdio/dashboard:latest`). There is no separate signal or relay container |
| NetBird release | Management server 0.79.0 (startup log, container started 3:00 AM on 2026-09-19); dashboard v2.93.0 (image label) |
| Live path | `/opt/docker/netbird` |
| Direct bindings | Dashboard `127.0.0.1:8080`; server `127.0.0.1:8081`; STUN `3478/udp` |
| Live URL | `https://netbird.alphasecunited.com`, NPM proxy host 1 |
| Internal DNS | `netbird.alphasecunited.com` resolves to `192.168.85.2` through UniFi |
| Reverse proxy | NPM at `172.31.85.10` on Docker network `proxy`; NetBird trusts only that address |
| Routing peer | `docker-network` (CT 107) is a peer (overlay `100.121.111.204`) and the sole router for the `AlphaSec-Galaxy` network, with masquerade |
| Reachable resources | `192.168.85.0/24` only. Twelve more resources exist but no policy grants them; see [Access-Network.md](Configuration/Access-Network.md) |
| Overlay DNS | Domain `netbird.selfhosted`. No nameserver groups, zones or records, so a remote peer reaches NPM by address but cannot resolve the `alphasecunited.com` names |
| VPN path | Validated 2026-07-12: a remote peer reached Access-A through the overlay (`ip route ... dev wt0`, HTTPS `200`) |

Both images track `latest`. The 0.78.1 to 0.79.0 and 2.92.0 to 2.93.0 moves have no change record; the container started at 3:00 AM on 2026-09-19, the time Dockhand's daily update runs.

## Changes

- 2026-09-04: management server 0.78.0 to 0.78.1, because 0.78.0 logged an outdated-version warning on every start. The dashboard stayed at v2.92.0. After the recreate the dashboard and `https://netbird.alphasecunited.com` returned `200`, and the local peer reconnected with relays `2/2 Available`.
- 2026-07-12: first peer, routed VPN path into Access-A, DNS-01 renewal path and bounded `json-file` logging (`10m`, 3 files) verified. [VPN-path record](Documentation/Change%20Records/First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md), [follow-ups and descope record](Documentation/Change%20Records/NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).
- 2026-07-10: deployed on CT 107 with NPM. [Deployment record](Documentation/Deployment.md).

## Records

- [Deployment record (2026-07-10)](Documentation/Deployment.md)
- [Change record: first peer and routed VPN path (2026-07-12)](Documentation/Change%20Records/First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md)
- [Change record: operational follow-ups and hardening descope (2026-07-12)](Documentation/Change%20Records/NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md)
- [Fleet maintenance record (2026-08-31)](../Ansible/Documentation/Change%20Records/Compose%20Fleet%20Maintenance%20-%202026-08-31.md)
- [Operations runbook](Documentation/Runbook.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Platform backlog](Documentation/TODO.md)
- [Configuration reference](Configuration/README.md)
- [Access-A network reference](Configuration/Access-Network.md)
- [Nginx Proxy Manager platform](../Nginx%20Proxy%20Manager/README.md)

## Layout

- `Documentation/`: deployment history, operating procedure, troubleshooting, and remaining work
- `Configuration/`: reader-editable Compose reference and configuration notes
- `Evidence/`: step screenshots from bounded jobs

## Network Boundaries

- The LXC uses key-only SSH. Root login, password SSH, and keyboard-interactive SSH are disabled.
- UniFi allows the LXC only the listed web and NTP egress before the catch-all Access-A external block.
