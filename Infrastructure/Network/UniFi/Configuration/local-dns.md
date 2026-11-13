# UniFi Local DNS

**Created:** 2026-07-11  
**Last updated:** 2026-11-12

The UniFi gateway answers these names for the LAN. Public authoritative DNS stays in Cloudflare and holds none of them. 28 records point at Nginx Proxy Manager on `docker-network` (`192.168.85.2`), five name the Galaxy nodes on MGMT-A, and one names Windows Admin Center on `HQ-MGT01`.

**Last verified against the controller:** 2026-11-05. `unifi_list_dns_records` returned 31 static records. On 2026-11-11 I added four, making 35. On 2026-11-12 I deleted `netbird`, and the list returned 34.

- 2026-09-27: I removed the `wud.alphasecunited.com` record with WUD retirement. The controller now holds 30 static records.

## Recent changes

- 2026-11-11: I added `desktop.e2b.alphasecunited.com` (`16d6e343-18a2-4cec-b806-a041542cc524`), A to `192.168.85.2`, the E2B Desktop viewer on NPM host 42. [Extra Templates and Disk Growth](../../../../Platforms/E2B/Documentation/Change%20Records/Extra%20Templates%20and%20Disk%20Growth%20-%202026-11-11.md).

- 2026-11-11: I added `e2b.alphasecunited.com` (`fa4e90f0-8ec5-4ab1-89af-7428e900102a`), `api.e2b.alphasecunited.com` (`0f41c33c-c3da-4416-80f0-974d524a74c1`) and `sandbox.e2b.alphasecunited.com` (`7e423abc-2a58-4e08-bff5-18674fe56a32`) for the E2B Embed trial, A records to `192.168.85.2`. Each resolves there from `ubuntu-dev`. E2B clients also need `E2B_SANDBOX_URL`, because the SDK otherwise addresses `<port>-<sandbox id>.e2b.alphasecunited.com` and these records cannot hold a wildcard. [Embed Trial Deployment](../../../../Platforms/E2B/Documentation/Change%20Records/Embed%20Trial%20Deployment%20-%202026-11-11.md).

- 2026-11-02: I added `book-digest.executor.apps.alphasecunited.com`, record `6ae87f44e2482aecb9604963`, the first Executor 2 app page. It resolves to `192.168.85.2`, where NPM wildcard host 38 forwards it to Executor. [App page domain](../../../../Platforms/Executor/Documentation/Change%20Records/App%20Page%20Domain%20-%202026-11-02.md).

- 2026-11-01: I deleted `dashboard.alphasecunited.com`, record `6ab90b1425574794b9328224`, when I retired Homarr. Neither the gateway at `192.168.1.1` nor `1.1.1.1` answers for the name. [Retirement](../../../../Archive/Platforms/Homarr/Documentation/Change%20Records/Retirement%20-%202026-11-01.md).

- 2026-10-31: I added `executor.alphasecunited.com` for Executor 2 through NPM, record `6ae628c8e2482aecb95a2c9b`, and deleted Executor 1's `mcp.alphasecunited.com`, record `6a94416df9e5db24858d3005`. The gateway resolver at `192.168.40.1` no longer answers for the old name. [Executor 2 Migration](../../../../Platforms/Executor/Documentation/Change%20Records/Executor%202%20Migration%20-%202026-10-31.md).

- 2026-10-05: I added `sure.alphasecunited.com` for Sure through NPM, record `6ac3e46b25574794b94ddd9b`. Before the change the controller listed 30 records with 24 pointing at NPM. [Sure deployment](../../../../Platforms/Sure/Documentation/Change%20Records/Deployment%20-%202026-10-05.md).

- 2026-09-27: I added `wud.alphasecunited.com` for Homarr's authenticated WUD connection, record `6ab91af825574794b932b0d5`. [Integration record](../../../../Archive/Platforms/Homarr/Documentation/Change%20Records/Media%20and%20Infrastructure%20Integrations%20-%202026-09-27.md).

- 2026-09-27: I recreated `dashboard.alphasecunited.com` for Homarr through NPM, record `6ab90b1425574794b9328224`. [Homarr deployment](../../../../Archive/Platforms/Homarr/Documentation/Change%20Records/Deployment%20-%202026-09-27.md).

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
| `booklore.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a844` | BookOrbit through NPM; legacy BookLore address retained |
| `sure.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6ac3e46b25574794b94ddd9b` | Sure on `docker-main` through NPM proxy host 36 |
| `forgejo.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a850` | Forgejo through NPM |
| `peanut.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a853` | PeaNUT through NPM |
| `wazuh.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a85a` | Wazuh dashboard through NPM |
| `grafana.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a862` | Grafana through NPM |
| `splunk.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a863` | Splunk Web through NPM |
| `prometheus.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a864` | Prometheus through NPM |
| `ts3-manager.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a68b26f052792cd2140bfdc` | TS3 Manager through NPM |
| `aiproxy.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a7a605fdee8c70a32dec053` | CLI Proxy API on `docker-main` through NPM |
| `executor.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6ae628c8e2482aecb95a2c9b` | Executor 2 on `docker-blue` through NPM proxy host 37 |
| `book-digest.executor.apps.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6ae87f44e2482aecb9604963` | Executor 2 app page through NPM wildcard proxy host 38 |
| `e2b.alphasecunited.com` | A | `192.168.85.2` | Controller default | Yes | `fa4e90f0-8ec5-4ab1-89af-7428e900102a` | E2B dashboard on `e2b-01` through NPM proxy host 39 |
| `api.e2b.alphasecunited.com` | A | `192.168.85.2` | Controller default | Yes | `0f41c33c-c3da-4416-80f0-974d524a74c1` | E2B API on `e2b-01` through NPM proxy host 40 |
| `sandbox.e2b.alphasecunited.com` | A | `192.168.85.2` | Controller default | Yes | `7e423abc-2a58-4e08-bff5-18674fe56a32` | E2B sandbox traffic (client-proxy) on `e2b-01` through NPM proxy host 41 |
| `desktop.e2b.alphasecunited.com` | A | `192.168.85.2` | Controller default | Yes | `16d6e343-18a2-4cec-b806-a041542cc524` | E2B Desktop viewer on `e2b-01` through NPM proxy host 42 |
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
| 2026-11-11 | `desktop.e2b` added | [Extra Templates and Disk Growth](../../../../Platforms/E2B/Documentation/Change%20Records/Extra%20Templates%20and%20Disk%20Growth%20-%202026-11-11.md) |
| 2026-11-11 | `e2b`, `api.e2b` and `sandbox.e2b` added | [Embed Trial Deployment](../../../../Platforms/E2B/Documentation/Change%20Records/Embed%20Trial%20Deployment%20-%202026-11-11.md) |
| 2026-11-02 | `book-digest.executor.apps` added | [App page domain](../../../../Platforms/Executor/Documentation/Change%20Records/App%20Page%20Domain%20-%202026-11-02.md) |
| 2026-10-31 | `executor` added; `mcp` removed | [Executor 2 Migration](../../../../Platforms/Executor/Documentation/Change%20Records/Executor%202%20Migration%20-%202026-10-31.md) |
| 2026-09-21 | `weebarr` added; absent by 2026-09-24 | [Weebarr Deployment](../../../../Archive/Platforms/Weebarr/Documentation/Change%20Records/Deployment%20-%202026-09-21.md) |
| 2026-09-15 | Dockge record replaced by `dockhand` | [Dockge Replacement](../../../../Platforms/Dockhand/Documentation/Change%20Records/Dockge%20Replacement%20-%202026-09-15.md) |
| 2026-09-13 | `mesh` added | [MeshCentral Internal HTTPS](../../../../Platforms/MeshCentral/Documentation/Change%20Records/Internal%20HTTPS%20Through%20Nginx%20Proxy%20Manager%20-%202026-09-13.md) |
| 2026-11-12 | `netbird` removed | [NetBird Retirement](../../../../Archive/Platforms/Netbird/Documentation/Change%20Records/Retirement%20-%202026-11-12.md) |
| 2026-09-12 | `hq-mgt01.ad` added | [WAC Deployment](../../../../Platforms/Windows%20Admin%20Center/Documentation/Change%20Records/Deployment%20-%202026-09-12.md) |
| 2026-09-12 | `games` and `wings` removed | [Game 01 Retirement](../../../../Archive/Platforms/Game%20Servers/Documentation/Change%20Records/Game%2001%20Retirement%20-%202026-09-12.md) |
| 2026-09-04 | `openwebui` added | [Open WebUI Internal HTTPS](../../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/Open%20WebUI%20Internal%20HTTPS%20-%202026-09-05.md) |
| 2026-08-30 | `mcp` added | [Executor Initial Deployment](../../../../Platforms/Executor/Documentation/Change%20Records/Initial%20Deployment%20-%202026-08-30.md) |
| 2026-08-19 | Kasm record deleted | [Kasm Workspaces Decommission](../../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md) |
| 2026-08-10 | `aiproxy` added | [CLI Proxy API Internal HTTPS](../../../../Platforms/CLI%20Proxy%20API/Documentation/Change%20Records/Internal%20HTTPS%20-%202026-08-10.md) |
| 2026-07-28 | `ts3-manager` added | [TS3 Manager Internal HTTPS](../../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/TS3%20Manager%20Internal%20HTTPS%20-%202026-07-28.md) |
| 2026-07-22 | First 19 application records | [Internal HTTPS Service Onboarding](../../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md) |
| 2026-07-11 | `netbird`, the first record | [NetBird deployment](../../../../Archive/Platforms/Netbird/Documentation/Deployment.md) |

On 2026-07-11 the `docker-network` LXC resolved `netbird` through its gateway resolver `192.168.85.1`, and a Windows client in Internal resolved the same record:

![Enabled UniFi internal DNS record showing the address and 300-second TTL](../../../../Archive/Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S06-UniFi-Internal-DNS-Record-2026-07-11.jpg)
