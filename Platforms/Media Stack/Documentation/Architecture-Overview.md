# Media Stack Architecture Overview

**Created:** 2026-07-17  
**Last updated:** 2026-07-18

## Purpose

I separate user-facing media workflows from download egress. Jellyfin, Seerr, Sonarr, Radarr, Prowlarr, and FlareSolverr use the guest's ordinary VLAN path. Only qBittorrent shares Gluetun's network namespace and therefore exits through Proton VPN.

```mermaid
flowchart LR
    U["LAN users"] --> JS["Seerr requests"]
    U --> JF["Jellyfin playback"]
    JS --> S["Sonarr"]
    JS --> R["Radarr"]
    P["Prowlarr"] --> S
    P --> R
    P -. "tagged challenge proxy" .-> F["FlareSolverr"]
    S --> Q["qBittorrent"]
    R --> Q
    Q --> G["Gluetun firewall + WireGuard"]
    G --> PV["Proton P2P endpoint"]
    PV --> I["Internet peers"]
    Q --> D["/data/downloads"]
    S --> TV["/data/media/tv"]
    R --> M["/data/media/movies"]
    TV --> JF
    M --> JF
```

## Resource and Device Model

I run CT 842 unprivileged, starting with the Proxmox node, on local LVM storage on `red-server`. It receives `/dev/dri/renderD128` for Jellyfin Intel Quick Sync and `/dev/net/tun` for the VPN tunnel. The guest has 4 vCPU, 8 GiB memory, 1 GiB swap, and a 100 GiB root volume.

Because the volume is node-local and the guest is not HA-managed, recovery depends on protected backups or restoration on `red-server`; automatic cross-node storage failover is not available.
