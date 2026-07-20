# Media Stack Deployment

**Created:** 2026-07-17  
**Last updated:** 2026-07-20

**Implementation date:** 2026-07-17  
**System:** Galaxy Proxmox cluster, `red-server`, CT 842 `media-01`  
**Status:** Infrastructure operational; application onboarding completed 2026-07-17 ([onboarding record](Media%20Stack%20Application%20Onboarding%20-%202026-07-17.md)); end-to-end acquisition test pending

## Scope

I deployed a dedicated 100 GiB media-automation LXC on VLAN 40 using Docker Compose, current container images, Jellyfin hardware acceleration, qBittorrent isolated behind Proton WireGuard, provider-side port forwarding, and FlareSolverr for selectively tagged indexer challenges. I left Bazarr out on purpose.

## Starting State

No dedicated media guest or platform record existed.

## Deployment Choices

1. **Use an unprivileged LXC on `red-server`.** The workload benefits from low overhead and direct device pass-through; I did not need full VM isolation for this trusted single-purpose stack.
2. **Use one 100 GiB local volume.** This is my explicit storage limit. Media, downloads, configuration, and transcodes therefore compete for the same capacity and require monitoring.
3. **Route only qBittorrent through Proton.** Indexer and media services keep ordinary LAN egress, while qBittorrent shares Gluetun's network namespace and kill switch.
4. **Enable Proton NAT-PMP, not router UPnP.** Proton assigns a port on the VPN endpoint. I keep qBittorrent's router-level UPnP/NAT-PMP disabled, and no UniFi inbound mapping is needed.
5. **Track `latest` images.** I track `latest` intentionally; it is my preference and it creates an explicit requirement for bounded, verified updates.
6. **Load deployment values from `.env`.** The Compose reference uses placeholders, while the live project reads `/opt/media-stack/.env`.

## Resulting Configuration

| Layer | Result |
| --- | --- |
| Proxmox | CT 842 `media-01`, 4 vCPU, 8 GiB memory, 1 GiB swap, 100 GiB `local-lvm`, unprivileged, on-boot |
| Network | VLAN 40, firewall enabled, address `192.168.40.42`, gateway `192.168.40.1` |
| Devices | `/dev/dri/renderD128` and `/dev/net/tun`, mode `0666` pass-through |
| OS | Debian GNU/Linux 13 (trixie) |
| Runtime | Docker Engine 29.6.2; Docker Compose 5.3.1 |
| Applications | Jellyfin, Jellyseerr, Sonarr, Radarr, Prowlarr, FlareSolverr, Gluetun, qBittorrent |
| Storage paths | `/opt/media-stack`, `/data/downloads`, `/data/media/movies`, `/data/media/tv`, `/data/transcodes` |

## Implementation and Verification

| Step | Action | Observed result |
| --- | --- | --- |
| S01 | Created and configured the unprivileged LXC | Guest running on `red-server`; resource, VLAN, firewall, startup, and device settings matched the table above |
| S02 | Applied the Linux host baseline | Approved-key SSH worked; root locked; root/password/keyboard-interactive SSH disabled; `<YOUR_ADMIN_USERNAME>` NOPASSWD sudo verified |
| S03 | Installed Docker and deployed the core services | Six non-VPN services running; Jellyfin healthy; service HTTP checks returned successful or expected redirect responses |
| S04 | Passed the Intel render device to Jellyfin | Intel iHD driver and H.264, HEVC Main 10, and VP9 hardware profiles observed in the container |
| S05 | Configured Prowlarr, Sonarr, Radarr, and FlareSolverr | Prowlarr application links saved; media root paths present; tagged FlareSolverr proxy available but not yet tested against a real challenge |
| S06 | Installed my Proton key and activated the VPN profile | Gluetun healthy; qBittorrent started only after Gluetun health; egress organization differed from the homelab ISP path |
| S07 | Verified provider-side port forwarding and kill-switch topology | Proton-assigned port equaled qBittorrent `listen_port`; `random_port=false`; `upnp=false`; qBittorrent network mode referenced Gluetun's container namespace |
| S08 | Linked qBittorrent to Sonarr and Radarr | Both download clients created and reachable using separate `sonarr` and `radarr` categories |
| S09 | Established the qBittorrent Web UI login | The new login worked, & the Sonarr and Radarr client tests passed |
| S10 | Performed final runtime and baseline inspection | Eight containers running; Gluetun and Jellyfin healthy; root/data volume 9% used |
| S11 | Recreated Gluetun and qBittorrent with an empty torrent queue | Gluetun returned healthy, qBittorrent returned running in Gluetun's exact namespace, the provider port resynchronized, and both auth-bypass controls persisted |

## Known Incomplete Items

- Jellyfin and Jellyseerr require first-run UI onboarding.
- Prowlarr has no indexers yet. Sonarr and Radarr therefore report expected RSS-sync errors and automatic-search warnings.
- No end-to-end request, download, import, and playback test has been completed.
- Backups and a restore test remain pending.

## Rollback

1. Stop the Compose project with the `vpn` profile.
2. Back up `/opt/media-stack/config` and `/data` if application state must be retained.
3. Remove CT 842 through the normal Proxmox guest-retirement workflow after confirming the exact target and backup disposition.
4. Remove the corresponding LXC and service inventory entries and archive this platform record.

Deleting the LXC destroys the only configured 100 GiB application and media volume, so I confirm the exact target and backup disposition before running it.
