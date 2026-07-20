# Media Stack Architecture Overview

**Created:** 2026-07-17  
**Last updated:** 2026-07-20

## Traffic Split

Jellyfin, Seerr, Sonarr, Radarr, Prowlarr, & FlareSolverr use the guest's VLAN 40 path. qBittorrent is the exception: it shares Gluetun's network namespace and exits through Proton VPN.

![Media Stack pipeline: LAN users reach Seerr for requests and Jellyfin for playback; Seerr and Prowlarr drive Sonarr and Radarr, which write to the tv and movie libraries that Jellyfin serves and hand downloads to qBittorrent; only qBittorrent egresses, through Gluetun and the Proton P2P endpoint out to internet peers](Diagrams/pipeline.svg)

## Resource and Device Model

I run CT 842 unprivileged, starting with the Proxmox node, on local LVM storage on `red-server`. It receives `/dev/dri/renderD128` for Jellyfin Intel Quick Sync and `/dev/net/tun` for the VPN tunnel. The guest has 4 vCPU, 8 GiB memory, 1 GiB swap, and a 100 GiB root volume.

Because the volume is node-local and the guest isn't HA-managed, recovery depends on backups or restoration on `red-server`; automatic cross-node storage failover isn't available.
