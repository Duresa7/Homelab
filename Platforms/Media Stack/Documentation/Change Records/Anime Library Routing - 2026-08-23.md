# Anime Library Routing

**Created:** 2026-08-23  
**Last updated:** 2026-08-23

**Implementation date:** 2026-08-23  
**System:** Galaxy Proxmox cluster, `red-server`, CT 842 `media-01`  
**Status:** Complete. Anime has its own Sonarr root, Jellyfin library, and Seerr request route. The first blocked partial-season import is corrected.

## What Changed

I created `/data/media/anime` on the HDD-backed `/data` filesystem with owner `dkadi:dkadi` and mode `0755`. I added that path as an accessible Sonarr root folder while retaining `/data/media/tv` for standard television.

I added a Jellyfin `Anime` shows library at `/media/anime`. It uses the same English, United States, real-time monitoring, season naming, subtitle, and scan settings as `TV Shows`, with automatic series grouping enabled. AniList is first in the Anime library's series metadata and image provider order, followed by the existing TMDB and OMDb providers where applicable. Jellyfin reported the AniList 13.0.0.0 plugin active.

I changed Seerr's default Sonarr server so standard series continue to use `/data/media/tv` and titles carrying TMDB's anime keyword use `/data/media/anime`. Both routes retain the `HD-1080p` quality profile. I resynced Seerr's Jellyfin libraries and enabled Anime alongside Movies and TV Shows.

Sonarr already classified two series as anime. I used Sonarr's move operation to relocate them on the same filesystem:

| Series | Resulting path |
| --- | --- |
| Mushoku Tensei: Jobless Reincarnation | `/data/media/anime/Mushoku Tensei - Jobless Reincarnation` |
| Star Wars: Visions Presents - The Ninth Jedi | `/data/media/anime/Star Wars - Visions Presents - The Ninth Jedi` |

The first Seerr update returned HTTP 400 because its API marks the body `id` field read-only. I removed that field from the request body, retained the ID in the route, and the update passed. No partial Seerr change remained from the rejected request.

## Verification

- Sonarr reported both `/data/media/tv` and `/data/media/anime` accessible.
- Both relocated series retained `seriesType=anime`, resolved under `/data/media/anime`, and their Sonarr `MoveSeries` commands completed successfully. The old paths were absent.
- The synced Sonarr indexer configuration retained Torznab anime category `5070`.
- Seerr's saved Sonarr settings reported `/data/media/anime` as the anime directory and `HD-1080p` as the anime profile.
- Seerr reported Anime, Movies, and TV Shows enabled in its Jellyfin library sync.
- A completed Jellyfin media-library scan returned both moved series from Anime and none from TV Shows. Anime had real-time monitoring enabled and AniList first in its series metadata and image provider order.
- Both current Jellyfin users had `EnableAllFolders=true`, so Anime required no per-user library grant.
- All eight Compose services remained running. Jellyfin and Gluetun remained healthy.
- The Anime tree contained 23 video files after the move. None retained a second link in `/data/downloads`, so there was no retained download payload available for a post-move hard-link comparison.
- A follow-up corrected a blocked 12-file Season 2 Part 2 import and cleared two stale completed qBittorrent records. Jellyfin then reported 35 Anime episodes across two series. The [troubleshooting record](../Troubleshooting/Anime%20Completed%20Downloads%20Missing%20from%20Jellyfin%20-%202026-08-23.md) holds the errors, episode mapping, and regression checks.

I kept no separate evidence folder for this change. I verified each resulting state through the live application APIs, filesystem, and Compose project during the implementation session.
