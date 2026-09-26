# UniFi Local DNS

**Created:** 2026-07-11  
**Last updated:** 2026-09-25

The UniFi gateway answers these names for the LAN. Public authoritative DNS stays in Cloudflare and holds none of them. 24 records point at Nginx Proxy Manager on `docker-network` (`192.168.85.2`), five name the Galaxy nodes on MGMT-A, and one names Windows Admin Center on `HQ-MGT01`.

**Last verified against the controller:** 2026-09-24. `unifi_list_dns_records` returned 30 static records, all enabled. The 24 NPM names match the 24 live NPM proxy hosts one for one.

## Recent changes

- 2026-09-24: no `weebarr.alphasecunited.com` record. I added it on 2026-09-21 and have no record of its removal. [Weebarr Retirement](../../../../Archive/Platforms/Weebarr/Documentation/Change%20Records/Retirement%20-%202026-09-25.md).
- 2026-09-19: I added `appportal.alphasecunited.com`. [Internal HTTPS record](../../../../Platforms/App%20Portal/Documentation/Change%20Records/Internal%20HTTPS%2C%20ObiPC%20Enrollment%20and%20the%20First%20Self-Update%20-%202026-09-19.md).
- 2026-09-16: I removed `portainer.alphasecunited.com` and added the missing `hq-mgt01.ad.alphasecunited.com` row. [Policy and DNS Readback](../Documentation/Change%20Records/Policy%20and%20DNS%20Readback%20-%202026-09-16.md).

## Host Records

| Hostname | Type | Value | TTL | Enabled | Record ID | Purpose |
|---|---|---|---:|---|---|---|
| `netbird.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a518ca70e10fae1225ad3ba` | Internal resolution for the NetBird dashboard through Nginx Proxy Manager on `docker-network` |
| `jellyfin.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a834` | Jellyfin through NPM |
| `seerr.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a837` | Seerr through NPM |
| `sonarr.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a83a` | Sonarr through NPM |
| `radarr.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a83d` | Radarr through NPM |
| `prowlarr.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a83e` | Prowlarr through NPM |
| `qbittorrent.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a83f` | qBittorrent through NPM |
| `semaphore.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a840` | Semaphore through NPM |
| `immich.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a841` | Immich through NPM |
| `booklore.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a844` | BookLore through NPM |
| `dashboard.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a84f` | Homelab dashboard through NPM host 12; its upstream `192.168.40.35:3001` has had no listener since 2026-09-22 |
| `forgejo.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a850` | Forgejo through NPM |
| `peanut.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a853` | PeaNUT through NPM |
| `wazuh.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a85a` | Wazuh dashboard through NPM |
| `grafana.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a862` | Grafana through NPM |
| `splunk.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a863` | Splunk Web through NPM |
| `prometheus.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a864` | Prometheus through NPM |
| `ts3-manager.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a68b26f052792cd2140bfdc` | TS3 Manager through NPM |
| `aiproxy.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a7a605fdee8c70a32dec053` | CLI Proxy API on `docker-main` through NPM |
| `mcp.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a94416df9e5db24858d3005` | Executor on `docker-blue` through NPM |
| `openwebui.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a9b3fe6f9e5db2485a29667` | Open WebUI on `docker-main` through NPM proxy host 28 |
| `dockhand.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6aa9de4e25574794b908a860` | Dockhand on `docker-main` through NPM proxy host 31 |
| `mesh.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6aa6313625574794b9fefb1b` | MeshCentral on `docker-blue` through NPM proxy host 29 |
| `appportal.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6aaed06c25574794b9154d90` | App Portal on `docker-main` through NPM proxy host 32 |
| `hq-mgt01.ad.alphasecunited.com` | A | `192.168.65.12` | 300 | Yes | `6aa4cfee80977b56f62991c0` | Windows Admin Center on `HQ-MGT01` |
| `grey.alphasecunited.com` | A | `192.168.70.10` | Controller default | Yes | `6a7dee01dee8c70a32e6ba96` | Proxmox GUI on `grey-server` |
| `purple.alphasecunited.com` | A | `192.168.70.11` | Controller default | Yes | `6a7dee43dee8c70a32e6bb43` | Proxmox GUI on `purple-server` |
| `blue.alphasecunited.com` | A | `192.168.70.12` | Controller default | Yes | `6a7deeabdee8c70a32e6bc70` | Proxmox GUI on `blue-server` |
| `red.alphasecunited.com` | A | `192.168.70.13` | Controller default | Yes | `6a7deee9dee8c70a32e6bd39` | Proxmox GUI on `red-server` |
| `green.alphasecunited.com` | A | `192.168.70.14` | Controller default | Yes | `6a7deefddee8c70a32e6bd6d` | Proxmox GUI on `green-server` |

## Records

| Date | Change | Record |
| --- | --- | --- |
| 2026-09-21 | `weebarr` added; absent by 2026-09-24 | [Weebarr Deployment](../../../../Archive/Platforms/Weebarr/Documentation/Change%20Records/Deployment%20-%202026-09-21.md) |
| 2026-09-15 | Dockge record replaced by `dockhand` | [Dockge Replacement](../../../../Platforms/Dockhand/Documentation/Change%20Records/Dockge%20Replacement%20-%202026-09-15.md) |
| 2026-09-13 | `mesh` added | [MeshCentral Internal HTTPS](../../../../Platforms/MeshCentral/Documentation/Change%20Records/Internal%20HTTPS%20Through%20Nginx%20Proxy%20Manager%20-%202026-09-13.md) |
| 2026-09-12 | `hq-mgt01.ad` added | [WAC Deployment](../../../../Platforms/Windows%20Admin%20Center/Documentation/Change%20Records/Deployment%20-%202026-09-12.md) |
| 2026-09-12 | `games` and `wings` removed | [Game 01 Retirement](../../../../Archive/Platforms/Game%20Servers/Documentation/Change%20Records/Game%2001%20Retirement%20-%202026-09-12.md) |
| 2026-09-04 | `openwebui` added | [Open WebUI Internal HTTPS](../../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/Open%20WebUI%20Internal%20HTTPS%20-%202026-09-05.md) |
| 2026-08-30 | `mcp` added | [Executor Initial Deployment](../../../../Platforms/Executor/Documentation/Change%20Records/Initial%20Deployment%20-%202026-08-30.md) |
| 2026-08-19 | Kasm record deleted | [Kasm Workspaces Decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |
| 2026-08-10 | `aiproxy` added | [CLI Proxy API Internal HTTPS](../../../../Platforms/CLI%20Proxy%20API/Documentation/Change%20Records/Internal%20HTTPS%20-%202026-08-10.md) |
| 2026-07-28 | `ts3-manager` added | [TS3 Manager Internal HTTPS](../../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/TS3%20Manager%20Internal%20HTTPS%20-%202026-07-28.md) |
| 2026-07-22 | First 19 application records | [Internal HTTPS Service Onboarding](../../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md) |
| 2026-07-11 | `netbird`, the first record | [NetBird deployment](../../../../Platforms/Netbird/Documentation/Deployment.md) |

On 2026-07-11 the `docker-network` LXC resolved `netbird` through its gateway resolver `192.168.85.1`, and a Windows client in Internal resolved the same record:

![Enabled UniFi internal DNS record showing the address and 300-second TTL](../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S06-UniFi-Internal-DNS-Record-2026-07-11.jpg)
