# UniFi Local DNS

**Created:** 2026-07-11  
**Last updated:** 2026-07-28

I track 21 local A records on the UniFi gateway. They send NetBird and 20 internal application names to Nginx Proxy Manager at `192.168.85.2`. Public authoritative DNS stays in Cloudflare and doesn't contain the 20 application names.

## Host Records

| Hostname | Type | Value | TTL | Enabled | Record ID | Purpose |
|---|---|---|---:|---|---|---|
| `<YOUR_NETBIRD_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `<YOUR_NETBIRD_DNS_RECORD_ID>` | Internal resolution for the NetBird dashboard through Nginx Proxy Manager on `docker-network` |
| `jellyfin.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a834` | Jellyfin through NPM |
| `seerr.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a837` | Seerr through NPM |
| `sonarr.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a83a` | Sonarr through NPM |
| `radarr.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a83d` | Radarr through NPM |
| `prowlarr.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a83e` | Prowlarr through NPM |
| `qbittorrent.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a83f` | qBittorrent through NPM |
| `semaphore.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2a2d027bb05525a840` | Semaphore through NPM |
| `immich.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a841` | Immich through NPM |
| `booklore.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a844` | BookLore through NPM |
| `dashboard.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a84f` | Homelab dashboard through NPM |
| `forgejo.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a850` | Forgejo through NPM |
| `portainer.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a852` | Portainer through NPM |
| `peanut.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a853` | PeaNUT through NPM |
| `syncthing.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a857` | Syncthing GUI through NPM |
| `wazuh.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a85a` | Wazuh dashboard through NPM |
| `grafana.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a862` | Grafana through NPM |
| `splunk.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a863` | Splunk Web through NPM |
| `prometheus.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a60fd2b2d027bb05525a864` | Prometheus through NPM |
| `kasm.<YOUR_BASE_DOMAIN>` | A | `192.168.85.2` | 300 | Yes | `6a69768d052792cd2140e39f` | Kasm Workspaces through NPM |

## Verification

I created and verified the record on 2026-07-11:

- The `docker-network` LXC resolved the record through its configured gateway resolver, `192.168.85.1`, and received `192.168.85.2`.
- A Windows Internal-zone client resolved the same A record to `192.168.85.2`.

![Enabled UniFi internal DNS record showing the address and 300-second TTL](../../../../../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S06-UniFi-Internal-DNS-Record-2026-07-11.jpg)

I added and verified the 19 application records on 2026-07-22. An Internal-zone Windows client resolved every name to `192.168.85.2`. Cloudflare DNS-over-HTTPS returned NXDOMAIN for all 19 names. The implementation is documented in the NPM [change record](../../../../../Platforms/Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

I added `kasm.<YOUR_BASE_DOMAIN>` on 2026-07-28 as record `6a69768d052792cd2140e39f`. A Windows client resolved it to `192.168.85.2`, & the HTTPS health endpoint returned `{"ok": true}` through NPM.

These records exist only on the UniFi resolver. They don't change the public Cloudflare zone.
