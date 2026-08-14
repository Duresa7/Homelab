# UniFi Local DNS

**Created:** 2026-07-11  
**Last updated:** 2026-08-13

I track 24 local A records on the UniFi gateway. Twenty-three enabled records send NetBird and internal application names to Nginx Proxy Manager at `192.168.85.2`. The disabled apex record is retained only as controller history. Public authoritative DNS stays in Cloudflare and doesn't contain the internal application names.

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
| `portainer.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a852` | Portainer through NPM |
| `peanut.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a853` | PeaNUT through NPM |
| `wazuh.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a85a` | Wazuh dashboard through NPM |
| `grafana.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a862` | Grafana through NPM |
| `splunk.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a863` | Splunk Web through NPM |
| `prometheus.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a864` | Prometheus through NPM |
| `ts3-manager.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a68b26f052792cd2140bfdc` | TS3 Manager through NPM |
| `kasm.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a69768d052792cd2140e39f` | Kasm Workspaces through NPM |
| `games.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a763e27dee8c70a32d41e33` | Pelican Panel on `game-01` through NPM |
| `wings.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a763e29dee8c70a32d41e41` | Pelican Wings API on `game-01` through NPM; the browser opens a console websocket straight to this name, so it needs its own HTTPS host rather than a path under `games` |
| `aiproxy.alphasecunited.com` | A | `192.168.85.2` | 300 | Yes | `6a7a605fdee8c70a32dec053` | CLI Proxy API on `ubuntu-dev` through NPM |
| `alphasecunited.com` | A | `192.168.1.1` | Controller default | No | Not retained | Disabled apex record; no client path depends on it |

## Verification

I created and verified the record on 2026-07-11:

- The `docker-network` LXC resolved the record through its configured gateway resolver, `192.168.85.1`, and received `192.168.85.2`.
- A Windows Internal-zone client resolved the same A record to `192.168.85.2`.

![Enabled UniFi internal DNS record showing the address and 300-second TTL](../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S06-UniFi-Internal-DNS-Record-2026-07-11.jpg)

I added and verified the first 19 application records on 2026-07-22. An Internal-zone Windows client resolved every name to `192.168.85.2`. Cloudflare DNS-over-HTTPS returned NXDOMAIN for all 19 names. The implementation is documented in the NPM [change record](../../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

I added `kasm.alphasecunited.com` on 2026-07-28 as record `6a69768d052792cd2140e39f`. A Windows client resolved it to `192.168.85.2`, & the HTTPS health endpoint returned `{"ok": true}` through NPM.

The 2026-08-03 audit found `ts3-manager.alphasecunited.com` enabled at NPM and UniFi, bringing the enabled set to 21. It also found the disabled apex record. Neither changes public DNS.

I added `games.alphasecunited.com` and `wings.alphasecunited.com` on 2026-08-07 for the game server platform, bringing the enabled set to 22. A Windows client on VLAN 50 resolved both to `192.168.85.2`. `games` returns HTTP 200 through NPM and `wings` returns 401, which is the Wings API rejecting an unauthenticated request rather than a proxy fault.

I added `aiproxy.alphasecunited.com` on 2026-08-10 for CLI Proxy API, bringing the enabled set to 23. `debian-dev` resolved it to `192.168.85.2`; HTTP redirected to HTTPS and HTTPS returned `200`. A public resolver returned no A record.

These records exist only on the UniFi resolver. They don't change the public Cloudflare zone.
