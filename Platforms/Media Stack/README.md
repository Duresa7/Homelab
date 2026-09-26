# Media Stack

**Created:** 2026-07-17  
**Last updated:** 2026-09-25

I run media requests, playback, release automation and VPN-isolated downloading from one Debian LXC, CT 842 `media-01` on `red-server`.

## Current State

Verified on the host on 2026-09-24.

| Item | Value |
| --- | --- |
| Guest | CT 842 `media-01` on `red-server`, VLAN 40, `192.168.40.42` |
| Resources | 2 vCPU, 4 GiB memory, 1 GiB swap ([tuned 2026-08-10](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Guest%20Resource%20Efficiency%20Tuning%20-%202026-08-10.md)) |
| Storage | 100 GiB NVMe root; 1 TB Seagate HDD at `/data` (916 GiB ext4) |
| Guest OS | Debian GNU/Linux 13 (trixie) |
| Compose project | `/opt/media-stack/compose.yml`, 8 containers |
| Beside it | cAdvisor, What's Up Docker and Hawser, each under `/opt/docker/<name>/` |
| Image policy | Application images track `latest`; I update them through the [runbook](Documentation/Runbook.md) |
| Internal HTTPS | Six names under `alphasecunited.com` through Nginx Proxy Manager |

## Services

| Service | Version, 2026-09-24 | Purpose | LAN port |
| --- | --- | --- | --- |
| Jellyfin | 12.1.0 | Library and playback, Intel Quick Sync | 8096 |
| Seerr | 3.4.1 | Requests; container still named `jellyseerr` | 5055 |
| Sonarr | 4.0.20.3014 | Television and anime | 8989 |
| Radarr | 6.4.4.10685 | Movies | 7878 |
| Prowlarr | 2.6.5.5623 | Indexers | 9696 |
| FlareSolverr | 3.5.2 | Challenge proxy for tagged indexers | Internal only |
| qBittorrent | 5.2.3 | Download client | 8080 through Gluetun |
| Gluetun | `latest`, no version label | Proton WireGuard tunnel, kill switch, forwarded port | Owns qBittorrent's network namespace |

qBittorrent runs with `network_mode: service:gluetun`, so its only path out is the Proton tunnel. Gluetun writes the provider's forwarded port into qBittorrent; the UniFi gateway has no port forward and UPnP stays off. Weebarr ran here from 2026-09-21 and is gone; its records are in the [archive](../../Archive/Platforms/Weebarr/README.md).

## Records

- [Architecture](Documentation/Architecture.md)
- [Operations runbook](Documentation/Runbook.md)
- [Configuration reference](Configuration/README.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Platform backlog](Documentation/TODO.md)
- [Verified Jellyfin and Sonarr settings](Documentation/Media%20Settings%20Research%20-%202026-07-17.md), 2026-07-17
- [Download payload-filtering research](Documentation/Download%20Payload%20Filtering%20Research%20-%202026-07-17.md), 2026-07-17
- [Deployment](Documentation/Change%20Records/Deployment%20-%202026-07-17.md), 2026-07-17
- [Refresh and payload filtering](Documentation/Change%20Records/Refresh%20and%20Payload%20Filtering%20-%202026-07-17.md), 2026-07-17
- [Application onboarding](Documentation/Change%20Records/Application%20Onboarding%20-%202026-07-17.md), 2026-07-17
- [HDD data migration](Documentation/Change%20Records/HDD%20Data%20Migration%20-%202026-07-22.md), 2026-07-22
- [Anime library routing](Documentation/Change%20Records/Anime%20Library%20Routing%20-%202026-08-23.md), 2026-08-23
- [Moonbase plugin installation](Documentation/Change%20Records/Moonbase%20Plugin%20Installation%20-%202026-08-26.md), 2026-08-26
- [Anime quality profile and custom formats](Documentation/Change%20Records/Anime%20Quality%20Profile%20and%20Custom%20Formats%20-%202026-08-27.md), 2026-08-27
- [Jellyfin 12 upgrade](Documentation/Change%20Records/Jellyfin%2012%20Upgrade%20-%202026-09-09.md), 2026-09-09
- [Container image updates](../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-13.md), 2026-09-13
- [Media Stack guide](../../Guides/Media-Stack.md)
