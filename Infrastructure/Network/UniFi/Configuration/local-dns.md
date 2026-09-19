# UniFi Local DNS

**Created:** 2026-07-11  
**Last updated:** 2026-09-19

On 2026-09-19 I added `appportal.alphasecunited.com` for App Portal behind Nginx Proxy Manager. The controller returns 30 static DNS records, 24 of them pointing at `192.168.85.2`. Both `ObiPC` and `HQ-WS001` resolve the name through the domain controllers and reach the portal over HTTPS. [Internal HTTPS record](../../../../Platforms/App%20Portal/Documentation/Change%20Records/Internal%20HTTPS%2C%20ObiPC%20Enrollment%20and%20the%20First%20Self-Update%20-%202026-09-19.md).

I removed portainer.alphasecunited.com on 2026-09-16. The controller now holds 29 static DNS records, 23 of them pointing at `192.168.85.2`, including the unchanged Dockhand record `6aa9de4e25574794b908a860`. The same readback returned `hq-mgt01.ad.alphasecunited.com`, which this table had not carried since the 2026-09-12 Windows Admin Center deployment, so I added its row without changing the controller.

On 2026-09-12 I removed `games.alphasecunited.com` and `wings.alphasecunited.com` for the Game 01 retirement. Their historical onboarding below does not describe an active endpoint.

On 2026-09-15 I replaced the Dockge A record with `dockhand.alphasecunited.com` pointing to NPM. The live controller returned 30 DNS records. HTTPS login and all six Hawser connections passed. [Replacement record](../../../../Platforms/Dockhand/Documentation/Change%20Records/Dockge%20Replacement%20-%202026-09-15.md).

On 2026-09-13 I added `mesh.alphasecunited.com` for MeshCentral behind Nginx Proxy Manager. The controller returned 28 records before the addition and 29 after, of which 23 point at `192.168.85.2`. This paragraph previously read 29 records with 24 pointing at Nginx Proxy Manager; that count had not been reduced when the two Game 01 names were removed on 2026-09-12, so I have replaced it with the live figures. Five records resolve the Galaxy Proxmox node names to their MGMT-A addresses. Public authoritative DNS stays in Cloudflare and doesn't contain these internal names.

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
| `dashboard.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a84f` | Homelab dashboard through NPM |
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

## Verification

I created and verified the record on 2026-07-11:

- The `docker-network` LXC resolved the record through its configured gateway resolver, `192.168.85.1`, and received `192.168.85.2`.
- A Windows Internal-zone client resolved the same A record to `192.168.85.2`.

![Enabled UniFi internal DNS record showing the address and 300-second TTL](../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S06-UniFi-Internal-DNS-Record-2026-07-11.jpg)

I added and verified the first 19 application records on 2026-07-22. An Internal-zone Windows client resolved every name to `192.168.85.2`. Cloudflare DNS-over-HTTPS returned NXDOMAIN for all 19 names. The implementation is documented in the NPM [change record](../../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

The 2026-08-03 audit found `ts3-manager.alphasecunited.com` enabled at NPM and UniFi, bringing the enabled set to 21. It also found the disabled apex record. Neither changes public DNS.

I added `games.alphasecunited.com` and `wings.alphasecunited.com` on 2026-08-07 for the game server platform, bringing the enabled set to 22. A Windows client on VLAN 50 resolved both to `192.168.85.2`. `games` returns HTTP 200 through NPM and `wings` returns 401, which is the Wings API rejecting an unauthenticated request rather than a proxy fault.

I added `aiproxy.alphasecunited.com` on 2026-08-10 for CLI Proxy API, bringing the enabled set to 23. `debian-dev` resolved it to `192.168.85.2`; HTTP redirected to HTTPS and HTTPS returned `200`. A public resolver returned no A record.

The record stayed unchanged when I moved the backend from `ubuntu-dev` to `docker-main` on 2026-08-19 because NPM remained the DNS target. After the move the HTTPS root and management page returned `200`, an unauthenticated model request returned `401`, and certificate verification returned `0`.

On 2026-08-19 I deleted the Kasm record with the retired platform. The same final controller readback showed that the disabled apex record was no longer present and captured five enabled Proxmox node records, leaving 27 enabled records and none disabled.

I added `mcp.alphasecunited.com` on 2026-08-30 for Executor, bringing the enabled set to 28. `docker-network` resolved it to `192.168.85.2`; HTTP redirected to HTTPS, the HTTPS health endpoint returned `200`, and Cloudflare DNS-over-HTTPS returned NXDOMAIN.

I added `openwebui.alphasecunited.com` on 2026-09-04 for Open WebUI, bringing the enabled set to 29. It resolves to NPM and has a narrow firewall path to `192.168.40.35:3002`. NPM proxy host 28 became active on 2026-09-05, its HTTPS health path returned `200`, and Cloudflare's public resolver returned NXDOMAIN.

These records exist only on the UniFi resolver. They don't change the public Cloudflare zone.
