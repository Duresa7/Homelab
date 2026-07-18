# Media Stack Application Onboarding Evidence

**Created:** 2026-07-17  
**Last updated:** 2026-07-17

**Capture window:** 2026-07-17, 20:08–21:14 EDT  
**Mechanism:** Operator-performed walkthrough in a workstation browser against the LAN management interfaces of CT 842 `media-01`

The onboarding was performed interactively in each application's web UI. No shell commands were part of the change, so no command transcript exists; the screenshots below are the complete retained evidence for this session. Credential and API-key fields visible during capture are masked by the applications' own interfaces, and no secret value appears in any image.

| Step | Evidence | Demonstrates |
| --- | --- | --- |
| S01 | [Jellyfin setup wizard](Screenshots/S01-Jellyfin-Setup-Wizard-Server-Name-2026-07-17.png) | Jellyfin's guided setup running with server name `Jelly-Media` and English display language |
| S02 | [Jellyfin Movies library](Screenshots/S02-Jellyfin-Movies-Library-Settings-2026-07-17.png) | `Movies` library (content type Movies) created enabled with English/United States metadata defaults and real-time monitoring; the folder picker is collapsed in the capture |
| S03 | [Jellyfin TV library](Screenshots/S03-Jellyfin-TV-Library-Settings-2026-07-17.png) | `TV Shows` library (content type Shows) created enabled with English/United States defaults and `Specials` season naming; the folder picker is collapsed in the capture |
| S04 | [qBittorrent baseline](Screenshots/S04-qBittorrent-WebUI-Baseline-Categories-2026-07-17.png) | Web UI reachable on the LAN address with an empty queue, existing `radarr` and `tv-sonarr` categories, 85.35 GiB free space, and DHT idle at zero nodes behind the VPN |
| S05 | [Jellyfin QSV transcoding](Screenshots/S05-Jellyfin-QSV-Transcoding-Settings-2026-07-17.png) | Intel QuickSync selected with a blank device field; hardware decoding enabled for H264, HEVC, MPEG2, VC1, VP8, VP9, HEVC 10-bit, and VP9 10-bit with AV1 and both HEVC RExt profiles off; OS-native VA-API decoders preferred; hardware encoding on with both Low-Power encoders off; HEVC output allowed. Tone-mapping fields sit below the captured viewport |
| S06 | [Sonarr episode naming](Screenshots/S06-Sonarr-Episode-Naming-2026-07-17.png) | Episode renaming with Smart Replace; standard, daily, and anime formats retaining `{Quality Full}`; season folders `Season {season}`; specials folder `Specials`; prefixed-range multi-episode style |
| S07 | [Sonarr root folder](Screenshots/S07-Sonarr-Root-Folder-TV-2026-07-17.png) | Television root folder `/data/media/tv` with 85.4 GiB free and zero unmapped folders; recycling bin unset with 7-day cleanup; permission rewriting off |
| S08 | [Sonarr download client](Screenshots/S08-Sonarr-Download-Client-Handling-2026-07-17.png) | `qBittorrent via Proton VPN` client enabled with completed-download handling and failed-download redownload on; no remote path mappings |
| S09 | [Radarr movie naming](Screenshots/S09-Radarr-Movie-Naming-Hardlinks-2026-07-17.png) | Movie renaming `{Movie Title} ({Release Year}) {Quality Full}`; hard-links-instead-of-copy enabled; 100 MB minimum-free-space import guard |
| S10 | [Radarr root folder](Screenshots/S10-Radarr-Root-Folder-Movies-2026-07-17.png) | Movie root folder `/data/media/movies` with 85.4 GiB free and zero unmapped folders |
| S11 | [Radarr profiles](Screenshots/S11-Radarr-Quality-Delay-Profiles-2026-07-17.png) | Six stock quality profiles with the default delay profile and no release profiles |
| S12 | [Radarr qBittorrent client detail](Screenshots/S12-Radarr-qBittorrent-Client-Detail-2026-07-17.png) | Download client entry pointing at host `gluetun` port 8080 with category `radarr` and no stored username, password, or API key; the Docker-subnet authentication bypass in the protected qBittorrent configuration covers this path |
| S13 | Screenshot not retained | No capture was retained for the Prowlarr indexer addition. The addition itself — one enabled public torrent indexer at priority 25 with the Standard sync profile, added 20:55, with no `flaresolverr` tag because the indexer does not require challenge handling — is recorded in the change record without retained evidence |
| S14 | [Seerr Jellyfin library sync](Screenshots/S14-Seerr-Jellyfin-Library-Sync-2026-07-17.png) | Seerr setup wizard signed in to Jellyfin with the Movies and TV Shows libraries synced and enabled; the Jellyfin API key is masked by the wizard |
| S15 | [Seerr Radarr connection](Screenshots/S15-Seerr-Radarr-Connection-Established-2026-07-17.png) | "Radarr connection established successfully" with Radarr as default server: host `radarr` port 7878, HD-1080p profile, root `/data/media/movies`, minimum availability Released, scan and automatic search enabled; API key masked |
| S16 | [Seerr Sonarr settings](Screenshots/S16-Seerr-Sonarr-Server-Settings-2026-07-17.png) | Sonarr as default server: host `sonarr` port 8989, HD-1080p profile for standard and anime series, root `/data/media/tv`, season folders on, scan and automatic search enabled; API key masked |
| S17 | [Seerr Discover populated](Screenshots/S17-Seerr-Discover-Populated-2026-07-17.png) | The migrated request UI rendering populated Discover metadata after wizard completion, confirming the post-migration interface is functional |

The bounded end-to-end acquisition test is not covered by this set: every qBittorrent capture shows an empty queue, and no request, grab, import, or playback capture exists. That test remains open in the [platform TODO](../../Documentation/TODO.md).
