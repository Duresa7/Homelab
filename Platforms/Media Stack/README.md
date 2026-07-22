# Media Stack

**Created:** 2026-07-17  
**Last updated:** 2026-07-22

I run request management, media playback, release automation, indexer coordination, challenge handling, & VPN-isolated downloading from one Debian LXC.

## Current State

| Item | Current value |
| --- | --- |
| Deployment status | Applications onboarded 2026-07-17; bounded end-to-end acquisition test passed 2026-07-21. Containers, Proton VPN tunnel, provider-side port forwarding, Sonarr/Radarr download-client links, Jellyfin libraries and QSV transcoding, Prowlarr indexers, and Seerr connections verified |
| Compute | Galaxy CT 842 `media-01` on `red-server` |
| Guest network | VLAN 40; address `192.168.40.42` |
| Guest resources | 4 vCPU, 8 GiB memory, 1 GiB swap, 100 GiB NVMe root volume, 1 TB HDD mounted at `/data` |
| Guest OS | Debian GNU/Linux 13 (trixie) |
| Live project | `/opt/media-stack` |
| HDD data paths | `/data/media/movies`, `/data/media/tv`, `/data/downloads`, `/data/transcodes` |
| Container policy | All application images intentionally track `latest`; updates are bounded and verified through the runbook |

## Services

| Service | Purpose | LAN port |
| --- | --- | --- |
| Jellyfin | Media library and playback | 8096 |
| Seerr | User request workflow; migrated from Jellyseerr | 5055 |
| Sonarr | Television automation | 8989 |
| Radarr | Movie automation | 7878 |
| Prowlarr | Indexer coordination | 9696 |
| FlareSolverr | Tagged challenge proxy; validated in use against an indexer that requires Cloudflare challenge handling | Internal only |
| qBittorrent | Download client | 8080 through Gluetun |
| Gluetun | Proton WireGuard tunnel, firewall kill switch, and provider-side port forwarding | Owns qBittorrent's network namespace |

qBittorrent has no independent container network path because I run it with `network_mode: service:gluetun`. Gluetun selects a Proton P2P endpoint, requests a forwarded port, and writes the active port into qBittorrent while keeping router-level UPnP/NAT-PMP disabled.

I pass `/dev/dri/renderD128` into the unprivileged guest so Jellyfin gets Intel Quick Sync, and `/dev/net/tun` for Gluetun's tunnel.

## Records

- [Architecture overview](Documentation/Architecture-Overview.md)
- [Deployment change record](Documentation/Change%20Records/Media%20Stack%20Deployment%20-%202026-07-17.md)
- [Refresh and payload-filtering change record](Documentation/Change%20Records/Media%20Stack%20Refresh%20and%20Payload%20Filtering%20-%202026-07-17.md)
- [Application onboarding change record](Documentation/Change%20Records/Media%20Stack%20Application%20Onboarding%20-%202026-07-17.md)
- [HDD data migration change record](Documentation/Change%20Records/Media%20Stack%20HDD%20Data%20Migration%20-%202026-07-22.md)
- [Operations runbook](Documentation/Runbook.md)
- [Verified Jellyfin and Sonarr settings](Documentation/Media%20Settings%20Research%20-%202026-07-17.md)
- [Download payload-filtering research](Documentation/Download%20Payload%20Filtering%20Research%20-%202026-07-17.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Platform backlog](Documentation/TODO.md)
- [Configuration reference](Configuration/README.md)

## Verified Data Path

I moved `/data` to the 1 TB HDD on 2026-07-22. The 100 GiB NVMe keeps `/opt/media-stack`, Docker, container layers, application configuration, databases, & Jellyfin cache. The HDD holds movies, television, downloads, & transcode scratch space through CT 842 `mp0`; Compose keeps the same guest paths.

The migration test wrote through qBittorrent, created a hard link between the download and media trees, read an existing movie, & encoded 10 seconds with Jellyfin's `h264_qsv` path. With the HDD unmounted, CT 842 failed startup before any application could write into an empty host directory.
