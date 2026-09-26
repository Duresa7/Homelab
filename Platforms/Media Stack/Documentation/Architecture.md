# Media Stack Architecture

**Created:** 2026-07-17  
**Last updated:** 2026-09-25

CT 842 `media-01` runs the whole stack on `red-server`. Every application uses the guest's VLAN 40 path except qBittorrent, which exits only through Proton VPN.

## Traffic Split

Jellyfin, Seerr, Sonarr, Radarr, Prowlarr and FlareSolverr use the guest's VLAN 40 path. qBittorrent shares Gluetun's network namespace and exits through Proton VPN. Nginx Proxy Manager at `192.168.85.2` fronts the six web UIs over internal HTTPS; UniFi allows it only TCP 5055, 7878, 8080, 8096, 8989 and 9696 to `media-01`. Sonarr writes standard television and anime to separate roots, Radarr writes movies, and Jellyfin serves all three as separate libraries.

![Media Stack: LAN clients reach Seerr for requests and Jellyfin for playback through Nginx Proxy Manager; Seerr and Prowlarr drive Sonarr and Radarr, which hand downloads to qBittorrent and write to the tv, anime and movie libraries that Jellyfin serves; only qBittorrent egresses, through Gluetun and the Proton P2P endpoint](../../../Assets/Diagrams/media-stack.svg)

## Resource and Device Model

CT 842 is an unprivileged container on `red-server` with startup enabled at the node. It receives `/dev/dri/renderD128` for Jellyfin Intel Quick Sync and `/dev/net/tun` for the VPN tunnel. On 2026-09-24 the guest had 2 vCPU, 4 GiB memory and 1 GiB swap, the size set in the [2026-08-10 tuning](../../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Guest%20Resource%20Efficiency%20Tuning%20-%202026-08-10.md), plus a 100 GiB NVMe-backed root volume.

## Storage Model

The NVMe root holds Debian, Docker, `/opt/media-stack`, container layers, application configuration, databases and Jellyfin cache. A 1 TB Seagate ST1000LM035 supplies `/data` through the host ext4 mount `/mnt/bindmounts/media-01-hdd` and CT 842 `mp0`. Movies, television, anime, downloads and transcodes share that filesystem, so Sonarr and Radarr hard-link completed downloads instead of copying them.

The HDD filesystem has 916 GiB usable capacity and is excluded from `vzdump`; I treat its media as replaceable. Its fstab-generated automount points at UUID `289788f9-52a4-4e49-885b-000e8d565c8b`. The bind source uses a `data` child that exists only on the mounted filesystem, so CT 842 fails startup when the HDD is not mounted.

The [2026-07-22 migration](Change%20Records/HDD%20Data%20Migration%20-%202026-07-22.md) proved the path: a qBittorrent write, a hard link between the download and media trees, a read of an existing movie and a 10-second `h264_qsv` encode all landed on the HDD. With the HDD unmounted, CT 842 failed startup before any application could write into an empty host directory.

Both volumes are node-local and the guest is not HA-managed. CT 842 cannot move to another Galaxy node without its NVMe root and HDD.
