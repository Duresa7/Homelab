# Weebarr

**Created:** 2026-09-21  
**Last updated:** 2026-09-25

**Status:** Retired. I removed Weebarr from `media-01` after the 2026-09-21 deployment; see the [retirement record](Documentation/Change%20Records/Retirement%20-%202026-09-25.md). The table below is the configuration as deployed.

I ran Weebarr 0.2.0 in the [media stack](../../../Platforms/Media%20Stack/README.md) on `media-01`, CT 842 at `192.168.40.42`. I verified the deployment on 2026-09-21.

| Item | Configuration |
| --- | --- |
| Address | [weebarr.alphasecunited.com](https://weebarr.alphasecunited.com), internal HTTPS |
| Direct listener | `http://192.168.40.42:18080` |
| Login | `dkadi`; the Weebarr admin item for media-01 |
| Container | `weebarr`, `ghcr.io/deepdaddyttv/weebarr:latest`, UID/GID `1000:1000` |
| Compose | `/opt/media-stack/compose.yml`, service `weebarr`, network `media` |
| Persistent settings | `/opt/media-stack/config/weebarr` mounted at `/config` |
| Backend | Seerr at `http://jellyseerr:5055` |
| Anime defaults | Sonarr server 0, profile 7 `[Anime] Remux-1080p`, `/data/media/anime`, series type `anime` |
| Requests | All seasons; automatic-request buckets disabled |
| Monitoring | Docker health check and Prometheus HTTPS blackbox probe |

Weebarr discovers seasonal anime through AniList and checks requests and availability through Seerr. Seerr uses the existing Sonarr, Prowlarr, VPN-isolated qBittorrent, and Jellyfin workflow. Weebarr needs no media-directory mount or direct downloader connection.

I used a local administrator login. On 2026-09-21 I changed its password to match my selected shared login and updated the Weebarr administrator item. Fresh HTTPS authentication and the Seerr connection test passed. Weebarr does not reuse Jellyfin's Moonbase/Seerr single sign-on. Login and backend credentials stay in the persistent application settings; the Compose definition contains no credential.

The [Compose fragment](Configuration/compose.fragment.yml) belongs inside the existing media-stack definition, which supplies the `media` network. Rebuilding on an empty config directory requires first-run login setup and the Seerr API key. Dockhand's saved definition at `/opt/docker/dockhand/stacks/imported/media_01/media-stack/compose.yaml` also includes this service.

The [deployment record](Documentation/Change%20Records/Deployment%20-%202026-09-21.md) contains the checks and removal path. Upstream maintains the [application documentation](https://deepdaddyttv.github.io/weebarr/) and [Seerr backend behavior](https://deepdaddyttv.github.io/weebarr/Backends/).
