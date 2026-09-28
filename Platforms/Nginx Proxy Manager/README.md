# Nginx Proxy Manager

**Created:** 2026-07-11  
**Last updated:** 2026-09-27

Nginx Proxy Manager (NPM) is my internal HTTPS front door. It runs on the `docker-network` LXC and serves every internal `*.alphasecunited.com` name with one Let's Encrypt DNS-01 wildcard certificate. It has no public DNS and no WAN ingress. Public traffic goes through Caddy on `edge-01` instead; see [Access Paths](../../Architecture/Access-Paths.md).

- 2026-09-27: I retired WUD proxy host 35 and verified the other 24 hosts remained. [Retirement](../Prometheus/Documentation/Change%20Records/WUD%20Retirement%20-%202026-09-27.md).

## Current State

Read back on 2026-09-24 unless a row says otherwise.

| Item | Current value |
|---|---|
| Compute | Galaxy CT 107 `docker-network`, Debian 13, `192.168.85.2`, VLAN 85 |
| NPM release | 2.15.1, pinned by tag and excluded from Dockhand updates since 2026-09-25 |
| Live path | `/opt/docker/nginx-proxy-manager` |
| Container | `nginx-proxy-manager`, healthy |
| Guest bindings | TCP 80, 81 and 443 |
| Docker network | External `proxy`, `172.31.85.0/24`; NPM fixed at `172.31.85.10` |
| Persistent data | `data/` and `letsencrypt/` bind mounts |
| Proxy hosts | 24 live (NetBird plus 23 applications), 11 soft-deleted on 2026-09-27; the list is in the [proxy-host inventory](Configuration/internal-proxy-hosts.md) |
| Shared certificate | Certificate 1, `*.alphasecunited.com` and `alphasecunited.com`, expires 2026-12-08 at 3:03 AM UTC; renews automatically through Cloudflare DNS-01 |
| Shared TLS policy | Every live host uses certificate 1 with Force SSL and HTTP/2; HSTS off |
| Local DNS | 24 UniFi A records point at `192.168.85.2`, one per live host |
| Administrator UI | `http://192.168.85.2:81`, no domain name |


## Changes

- 2026-09-27: I added WUD HTTPS as proxy host 35 for the [Homarr integration](../Homarr/Documentation/Change%20Records/Media%20and%20Infrastructure%20Integrations%20-%202026-09-27.md).

- 2026-09-27: I added Homarr as proxy host 34 at `dashboard.alphasecunited.com`, HTTP backend `192.168.40.35:7575`, and verified all 24 HTTPS hosts. [Deployment](../Homarr/Documentation/Change%20Records/Deployment%20-%202026-09-27.md).

- 2026-09-26: I removed dashboard proxy host 12, its DNS record, and TCP 3001 from the backend policy. [Retirement](../../Archive/Platforms/Homelab%20Dashboard/Documentation/Change%20Records/Retirement%20-%202026-09-26.md).

- 2026-09-25: a scheduled Dockhand update stopped NPM and could not restart it. Everything behind `192.168.85.2` was down from 3:00 AM to 6:12 AM. I pinned the image to 2.15.1 and set `dockhand.update: "false"`. [Incident](../../Security/Incidents/Nginx%20Proxy%20Manager/Scheduled%20Update%20Stranded%20the%20Proxy%20-%202026-09-25.md).
- 2026-09-21 to 2026-09-24: Weebarr proxy host 33 was added on 2026-09-21 and was soft-deleted by 2026-09-24. [Archived Weebarr record](../../Archive/Platforms/Weebarr/README.md).
- 2026-09-19: proxy host 32, `appportal.alphasecunited.com`, forwards to `192.168.40.35:3004`. The UniFi policy `Allow NPM to docker-main web UIs` needed TCP 3004 first. [Record](../App%20Portal/Documentation/Change%20Records/Internal%20HTTPS%2C%20ObiPC%20Enrollment%20and%20the%20First%20Self-Update%20-%202026-09-19.md).
- 2026-09-16: removed Portainer proxy host 14.
- 2026-09-15: replaced Dockge host 30 with Dockhand host 31 (`192.168.40.35:3003`, WebSockets on). [Record](../Dockhand/Documentation/Change%20Records/Dockge%20Replacement%20-%202026-09-15.md).
- 2026-09-13: proxy host 29, `mesh.alphasecunited.com`, forwards over HTTPS to MeshCentral at `192.168.40.39:443`. It was the first host with an HTTPS backend. [Record](../MeshCentral/Documentation/Change%20Records/Internal%20HTTPS%20Through%20Nginx%20Proxy%20Manager%20-%202026-09-13.md).
- 2026-09-12: retired proxy hosts 24 (`games`) and 25 (`wings`) with the game-01 retirement.

## Records

- [Deployment record (2026-07-10)](Documentation/Deployment.md)
- [Operations runbook](Documentation/Runbook.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Platform backlog](Documentation/TODO.md)
- [Configuration reference](Configuration/README.md)
- [Internal proxy-host inventory](Configuration/internal-proxy-hosts.md)
- [Internal HTTPS service onboarding (2026-07-22)](Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md)
- [TS3 Manager internal HTTPS (2026-07-28)](Documentation/Change%20Records/TS3%20Manager%20Internal%20HTTPS%20-%202026-07-28.md)
- [Error log cleanup (2026-08-19)](Documentation/Change%20Records/Error%20Log%20Cleanup%20-%202026-08-19.md)
- [Open WebUI internal HTTPS (2026-09-05)](Documentation/Change%20Records/Open%20WebUI%20Internal%20HTTPS%20-%202026-09-05.md)
- [CLI Proxy API internal HTTPS (2026-08-10)](../CLI%20Proxy%20API/Documentation/Change%20Records/Internal%20HTTPS%20-%202026-08-10.md)
- [CLI Proxy API relocation to docker-main (2026-08-19)](../CLI%20Proxy%20API/Documentation/Change%20Records/Relocation%20to%20docker-main%20-%202026-08-19.md)
- [NetBird and NPM operational follow-ups and hardening descope (2026-07-12)](../Netbird/Documentation/Change%20Records/NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md)
- [NetBird platform](../Netbird/README.md)

## Network Boundaries

- NetBird trusts only `172.31.85.10/32` as its HTTP proxy.
- TCP 80, 81 and 443 bind on `192.168.85.2`. No WAN ingress points at the guest.
- UniFi permits NPM only to each backend's listed web ports. On 2026-09-24, 13 policies named NPM: ten from NPM to a backend, three from clients (two Hawser agents and HQ-WS001) to NPM on 443.
- NPM's `Public` access-list label means no NPM access list is assigned. It does not mean public DNS or an Internet path.
