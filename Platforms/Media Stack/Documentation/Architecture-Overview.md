# Media Stack Architecture Overview

**Created:** 2026-07-17  
**Last updated:** 2026-07-22

## Traffic Split

Jellyfin, Seerr, Sonarr, Radarr, Prowlarr, & FlareSolverr use the guest's VLAN 40 path. qBittorrent is the exception: it shares Gluetun's network namespace and exits through Proton VPN.

![Media Stack pipeline: LAN users reach Seerr for requests and Jellyfin for playback; Seerr and Prowlarr drive Sonarr and Radarr, which write to the tv and movie libraries that Jellyfin serves and hand downloads to qBittorrent; only qBittorrent egresses, through Gluetun and the Proton P2P endpoint out to internet peers](Diagrams/pipeline.svg)

## Resource and Device Model

I run CT 842 as an unprivileged container on `red-server`, with startup enabled at the Proxmox node. It receives `/dev/dri/renderD128` for Jellyfin Intel Quick Sync & `/dev/net/tun` for the VPN tunnel. The guest has 4 vCPU, 8 GiB memory, 1 GiB swap, & a 100 GiB NVMe-backed root volume.

## Storage Model

The NVMe root holds Debian, Docker, `/opt/media-stack`, container layers, application configuration, databases, & Jellyfin cache. A 1 TB Seagate ST1000LM035 supplies `/data` through the host ext4 mount `/mnt/bindmounts/media-01-hdd` and CT 842 `mp0`. Movies, television, downloads, & transcodes share that filesystem, so Sonarr and Radarr can hard-link completed downloads instead of copying them.

The HDD filesystem has 916 GiB usable capacity & isn't included in `vzdump`; I treat its media as replaceable. Its fstab-generated automount points at UUID `289788f9-52a4-4e49-885b-000e8d565c8b`. The bind source uses a `data` child that exists only on the mounted filesystem, so CT 842 fails startup when the HDD isn't mounted.

Both volumes are node-local, & the guest isn't HA-managed. CT 842 can't move to another Galaxy node without its NVMe root & HDD.
