# Media Stack Application Onboarding

**Created:** 2026-07-17  
**Last updated:** 2026-07-18

**Implementation date:** 2026-07-17  
**System:** Galaxy Proxmox cluster, `red-server`, CT 842 `media-01`  
**Status:** Complete; the bounded end-to-end acquisition test remains open in the [platform TODO](../TODO.md)

## Scope

I completed the UI-guided application onboarding deferred by my [deployment record](Media%20Stack%20Deployment%20-%202026-07-17.md) and carried through the [refresh record](Media%20Stack%20Refresh%20and%20Payload%20Filtering%20-%202026-07-17.md): Jellyfin's guided setup, media libraries, and hardware transcoding; Sonarr and Radarr media management; the first Prowlarr indexer; and confirmation of the migrated Seerr connections to Jellyfin, Sonarr, and Radarr.

## Method and Evidence Boundary

I performed the entire onboarding interactively in each application's web UI between 20:08 and 21:14 EDT on 2026-07-17. No shell commands were part of this change, so no command transcript exists; the retained evidence is the 16-screenshot set catalogued in the [evidence index](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Evidence-Index.md). The applications themselves mask API-key fields shown during setup, and no secret value appears in the captures. I did not retain a screenshot for the S13 Prowlarr indexer addition, so that step is recorded without retained evidence.

## Actions and Results

| Step | Action | Observed result |
| --- | --- | --- |
| S01 | Completed Jellyfin's guided setup | Server name `Jelly-Media` with English display language |
| S02–S03 | Added the Jellyfin libraries | `Movies` (content type Movies) and `TV Shows` (content type Shows) created enabled with English/United States metadata defaults, real-time monitoring, and `Specials` season naming; the folder pickers are collapsed in the captures, and both libraries subsequently appeared in Seerr's library sync (S14) |
| S04 | Confirmed the qBittorrent baseline | Web UI reachable on the LAN address; empty queue; existing `radarr` and `tv-sonarr` categories; 85.35 GiB free; DHT idle at zero nodes behind the VPN |
| S05 | Applied the researched Quick Sync transcoding selections | Intel QuickSync with a blank device field; hardware decoding enabled for H264, HEVC, MPEG2, VC1, VP8, VP9, HEVC 10-bit, and VP9 10-bit with AV1 and both HEVC RExt profiles off; OS-native VA-API decoders preferred; hardware encoding on with both Intel Low-Power encoders off; HEVC output allowed, matching my [media settings research](../Media%20Settings%20Research%20-%202026-07-17.md) |
| S06–S07 | Set Sonarr media management | Episode renaming with Smart Replace; standard, daily, and anime formats retaining `{Quality Full}`; season folders `Season {season}`; root folder `/data/media/tv` with 85.4 GiB free and zero unmapped folders |
| S08 | Verified Sonarr's download-client wiring | `qBittorrent via Proton VPN` enabled; completed-download handling on; failed-download redownload on, including from interactive search; no remote path mappings |
| S09–S11 | Set Radarr media management and profiles | Movie renaming `{Movie Title} ({Release Year}) {Quality Full}` with matching folder format; hard-links-instead-of-copy enabled; 100 MB minimum-free-space import guard; root folder `/data/media/movies`; six stock quality profiles with the default delay profile |
| S12 | Verified Radarr's qBittorrent client entry | Host `gluetun` port 8080 with category `radarr` and no stored username, password, or API key in the client entry; the Docker-subnet authentication bypass in qBittorrent's protected configuration covers this path per my [configuration reference](../../Configuration/README.md) |
| S13 | Added the first Prowlarr indexer | One public torrent indexer enabled at priority 25 with the Standard sync profile at 20:55, syncing to Sonarr and Radarr through the application links established at deployment; I did not apply the `flaresolverr` tag because this indexer does not require challenge handling. No screenshot retained; see the [evidence index](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Evidence-Index.md) |
| S14–S16 | Completed Seerr's setup wizard | Jellyfin sign-in and library sync with Movies and TV Shows enabled; Radarr added as default server with a "connection established successfully" result, HD-1080p profile, root `/data/media/movies`, and minimum availability Released; Sonarr configured as default server with HD-1080p for standard and anime series, root `/data/media/tv`, and season folders on |
| S17 | Confirmed the migrated request UI | Seerr's Discover view renders populated metadata after wizard completion, confirming the post-migration interface is functional and closing the Seerr-connection item from the refresh record's remaining verification |

## Step Evidence

<details>
<summary>Step S01 screenshot: Jellyfin setup wizard, server name</summary>

![Jellyfin guided setup with server name Jelly-Media and English display language](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S01-Jellyfin-Setup-Wizard-Server-Name-2026-07-17.png)

</details>

<details>
<summary>Step S02 screenshot: Jellyfin Movies library</summary>

![Movies library created enabled with English/United States metadata defaults and real-time monitoring; folder picker collapsed](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S02-Jellyfin-Movies-Library-Settings-2026-07-17.png)

</details>

<details>
<summary>Step S03 screenshot: Jellyfin TV library</summary>

![TV Shows library created enabled with English/United States defaults and Specials season naming; folder picker collapsed](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S03-Jellyfin-TV-Library-Settings-2026-07-17.png)

</details>

<details>
<summary>Step S04 screenshot: qBittorrent baseline</summary>

![qBittorrent Web UI reachable with an empty queue, radarr and tv-sonarr categories, 85.35 GiB free, and DHT idle behind the VPN](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S04-qBittorrent-WebUI-Baseline-Categories-2026-07-17.png)

</details>

<details>
<summary>Step S05 screenshot: Jellyfin QSV transcoding</summary>

![Intel QuickSync transcoding with the researched decode and encode selections; tone-mapping fields sit below the captured viewport](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S05-Jellyfin-QSV-Transcoding-Settings-2026-07-17.png)

</details>

<details>
<summary>Step S06 screenshot: Sonarr episode naming</summary>

![Sonarr episode renaming with Smart Replace and Season {season} folders](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S06-Sonarr-Episode-Naming-2026-07-17.png)

</details>

<details>
<summary>Step S07 screenshot: Sonarr root folder</summary>

![Sonarr television root folder /data/media/tv with 85.4 GiB free and zero unmapped folders](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S07-Sonarr-Root-Folder-TV-2026-07-17.png)

</details>

<details>
<summary>Step S08 screenshot: Sonarr download client</summary>

![Sonarr qBittorrent via Proton VPN client enabled with completed-download handling and failed-download redownload on](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S08-Sonarr-Download-Client-Handling-2026-07-17.png)

</details>

<details>
<summary>Step S09 screenshot: Radarr movie naming and hard-links</summary>

![Radarr movie naming with hard-links-instead-of-copy enabled and a 100 MB minimum-free-space import guard](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S09-Radarr-Movie-Naming-Hardlinks-2026-07-17.png)

</details>

<details>
<summary>Step S10 screenshot: Radarr root folder</summary>

![Radarr movie root folder /data/media/movies with 85.4 GiB free and zero unmapped folders](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S10-Radarr-Root-Folder-Movies-2026-07-17.png)

</details>

<details>
<summary>Step S11 screenshot: Radarr quality and delay profiles</summary>

![Radarr six stock quality profiles with the default delay profile and no release profiles](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S11-Radarr-Quality-Delay-Profiles-2026-07-17.png)

</details>

<details>
<summary>Step S12 screenshot: Radarr qBittorrent client detail</summary>

![Radarr download-client entry pointing at host gluetun port 8080 with category radarr and no stored credential](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S12-Radarr-qBittorrent-Client-Detail-2026-07-17.png)

</details>

S13 has no retained screenshot, as recorded above.

<details>
<summary>Step S14 screenshot: Seerr Jellyfin library sync</summary>

![Seerr setup wizard signed in to Jellyfin with the Movies and TV Shows libraries synced and enabled](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S14-Seerr-Jellyfin-Library-Sync-2026-07-17.png)

</details>

<details>
<summary>Step S15 screenshot: Seerr Radarr connection</summary>

![Seerr Radarr connection established with Radarr as default server](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S15-Seerr-Radarr-Connection-Established-2026-07-17.png)

</details>

<details>
<summary>Step S16 screenshot: Seerr Sonarr settings</summary>

![Seerr Sonarr default-server settings with HD-1080p for standard and anime series and season folders on](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S16-Seerr-Sonarr-Server-Settings-2026-07-17.png)

</details>

<details>
<summary>Step S17 screenshot: Seerr Discover populated</summary>

![Migrated Seerr request UI rendering populated Discover metadata after wizard completion](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S17-Seerr-Discover-Populated-2026-07-17.png)

</details>

## Deviations and Uncaptured Items

- The Sonarr naming formats keep the season folder as `Season {season}` and omit the `{Release Group}` token; my [media settings research](../Media%20Settings%20Research%20-%202026-07-17.md) recommends `Season {season:00}` and retaining the release group. I will adopt or explicitly decline those refinements no later than the end-to-end test.
- Sonarr's advanced Importing section (hard-link toggle) and Jellyfin's tone-mapping selections sit below the captured viewports. Radarr's hard-link setting is confirmed enabled; I verify Sonarr hard-linking and the researched OpenCL/BT.2390 tone-mapping selections during the end-to-end test.
- The Jellyfin library folder pickers are collapsed in S02–S03; the Arr root folders and the Seerr library sync corroborate the `/data/media` paths indirectly.
- I did not re-capture the Sonarr and Radarr indexer health banners after the Prowlarr sync; the pre-onboarding warnings are recorded in my [troubleshooting log](../Troubleshooting-Log.md) and should now be clear.

## Remaining Verification

I still need to run the bounded end-to-end test tracked in the [platform TODO](../TODO.md): one television and one movie request through Seerr, Prowlarr search, qBittorrent transfer inside the VPN namespace, hard-link import, and Jellyfin playback with the GPU active, inspecting qBittorrent's Content list against the payload filter during the transfer. FlareSolverr's real-indexer challenge validation stays pending until an indexer actually requires it.

## Rollback

Every change is an application-level UI setting: I can revert individual selections in place (library removal in Jellyfin, indexer removal in Prowlarr, server removal in Seerr, per-setting reversion in the Arr applications) without touching Compose, images, or the VPN path. No infrastructure change occurred.
