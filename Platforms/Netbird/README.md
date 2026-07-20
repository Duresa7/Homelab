# NetBird

**Created:** 2026-07-11  
**Last updated:** 2026-07-20

I run NetBird and Nginx Proxy Manager in Debian 13 LXC 107 `docker-network`. The control plane, reverse proxy, & certificate path share one VLAN 85 host instead of the existing `docker-blue` workload container.

## Current State

| Item | Current value |
|---|---|
| Deployment status | Operational over HTTPS; authenticated dashboard, controlled Compose restart, routed VPN path, automated renewal, and bounded logging verified |
| Compute | Galaxy CT 107 `docker-network` on VLAN 85 |
| Guest address | `192.168.85.2/24` |
| NetBird release | v0.74.4 (updated 2026-07-12 from the 0.74.3 initial install); deployed from the official installer |
| Live path | `/opt/docker/netbird` |
| Containers | `netbird-dashboard`, `netbird-server` |
| Direct bindings | Dashboard `127.0.0.1:8080`; server `127.0.0.1:8081`; STUN `3478/udp` |
| Live URL | `https://<YOUR_NETBIRD_DOMAIN>` |
| Internal DNS | `<YOUR_NETBIRD_DOMAIN>` resolves to `192.168.85.2` through UniFi |
| Reverse proxy | Online Nginx Proxy Manager host through `172.31.85.10` on Docker network `proxy` |
| Routing peer | `docker-network` (CT 107) is a NetBird peer (overlay `100.121.111.204`) advertising the `<YOUR_ORG_NAME>-Access` network `192.168.85.0/24` with masquerade |
| VPN path | Validated 2026-07-12; a remote peer reaches Access-A through the overlay via the routing peer (`ip route ... dev wt0`, HTTPS `200`) |

The embedded identity provider and dashboard return HTTP `200` on their direct local checks. The saved Nginx Proxy Manager host is Online, its advanced routes pass `nginx -t`, and its Let's Encrypt wildcard/apex certificate was issued through Cloudflare DNS-01. Force SSL and HTTP/2 are enabled, the intended HTTPS URL returns `200`, and I confirmed the authenticated NetBird administrator dashboard in Chrome. My controlled restarts of both Compose projects finished with Nginx Proxy Manager healthy, both NetBird containers running, and HTTPS still returning `200`.

Initial publication, first-peer enrollment, the routed VPN path into Access-A, the non-interactive DNS-01 renewal path, and bounded `json-file` logging (`10m` × `3`) are verified. See the [VPN-path change record](Documentation/Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md) and the [operational follow-ups and descope record](Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).

## Records

- [Deployment record](Documentation/Deployment.md)
- [Change record: first peer and routed VPN path (2026-07-12)](Documentation/Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md)
- [Change record: operational follow-ups and hardening descope (2026-07-12)](Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md)
- [Operations runbook](Documentation/Runbook.md)
- [Troubleshooting log](Documentation/Troubleshooting-Log.md)
- [Platform backlog](Documentation/TODO.md)
- [Configuration reference](Configuration/README.md)
- [Access-A network reference](Configuration/Access-Network.md)
- [Nginx Proxy Manager platform](../Nginx%20Proxy%20Manager/README.md)

## Layout

- `Documentation/`: deployment history, operating procedure, troubleshooting, and remaining work
- `Configuration/`: reader-editable Compose reference and configuration notes
- `Evidence/`: step screenshots from bounded jobs

## Network Boundaries

- NetBird trusts only Nginx Proxy Manager's fixed Docker address, `172.31.85.10/32`, as an HTTP proxy.
- The LXC uses key-only SSH. Root login, password SSH, and keyboard-interactive SSH are disabled.
- UniFi allows the LXC only the approved web and NTP egress before the catch-all Access-A external block.
