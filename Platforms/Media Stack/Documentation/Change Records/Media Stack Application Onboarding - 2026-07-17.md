# Media Stack Application Onboarding

**Created:** 2026-07-17  
**Last updated:** 2026-07-22

**Implementation date:** 2026-07-17  
**System:** Galaxy Proxmox cluster, `red-server`, CT 842 `media-01`  
**Status:** Complete. The bounded end-to-end acquisition test passed in full on 2026-07-21 (television and movie, hard-link import, payload-filter check, GPU-active playback); the one retained capture is the Jellyfin movie library.

## Scope

I completed Jellyfin's guided setup, media libraries, & hardware transcoding; Sonarr and Radarr media management; the first Prowlarr indexer; & the migrated Seerr connections to Jellyfin, Sonarr, & Radarr. The [deployment record](Media%20Stack%20Deployment%20-%202026-07-17.md) and [refresh record](Media%20Stack%20Refresh%20and%20Payload%20Filtering%20-%202026-07-17.md) cover the infrastructure that came first.

## UI Session and Screenshots

I performed the onboarding in each application's web UI between 20:08 & 21:14 EDT on 2026-07-17. The [evidence index](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Evidence-Index.md) catalogs 16 screenshots. Step 13 has no screenshot.

## Walkthrough

### Step 1: Complete the Jellyfin welcome screen

**UI path and action:** In Jellyfin Setup Wizard > Welcome, I set the server name to `Jelly-Media`, selected English as the display language, and continued.

**Observed result:** The wizard accepted the server identity and language settings.

**Verification:** I confirmed both values on the welcome screen before continuing.

**Evidence:**

![Jellyfin guided setup with server name Jelly-Media and English display language](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S01-Jellyfin-Setup-Wizard-Server-Name-2026-07-17.png)

### Step 2: Add the Jellyfin Movies library

**UI path and action:** In Jellyfin Setup Wizard > Set up your media libraries > Add Media Library, I created `Movies` with content type Movies, English and United States metadata defaults, and real-time monitoring enabled.

**Observed result:** Jellyfin saved the library as enabled. The folder picker is collapsed in the retained capture.

**Verification:** The `Movies` library later appeared and was enabled during Seerr's Jellyfin library sync in Step 14.

**Evidence:**

![Configured Add Media Library dialog for Movies with English and United States metadata defaults and real-time monitoring; folder picker collapsed](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S02-Jellyfin-Movies-Library-Settings-2026-07-17.png)

### Step 3: Add the Jellyfin TV Shows library

**UI path and action:** In Jellyfin Setup Wizard > Set up your media libraries > Add Media Library, I created `TV Shows` with content type Shows, English and United States metadata defaults, real-time monitoring, and `Specials` season naming.

**Observed result:** Jellyfin saved the library as enabled. The folder picker is collapsed in the retained capture.

**Verification:** The `TV Shows` library later appeared and was enabled during Seerr's Jellyfin library sync in Step 14.

**Evidence:**

![Configured Add Media Library dialog for TV Shows with English and United States defaults and Specials season naming; folder picker collapsed](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S03-Jellyfin-TV-Library-Settings-2026-07-17.png)

### Step 4: Check the qBittorrent baseline

**UI path and action:** In qBittorrent Web UI > Transfers, I reviewed the queue, categories, free space, and DHT state before wiring the Arr applications to the client.

**Observed result:** The UI was reachable with an empty queue, the `radarr` and `tv-sonarr` categories present, 85.35 GiB free, and DHT idle at zero nodes behind the VPN.

**Verification:** The LAN UI displayed an empty queue, categories `radarr` & `tv-sonarr`, 85.35 GiB free, & DHT at zero nodes.

**Evidence:**

![qBittorrent Web UI reachable with an empty queue, radarr and tv-sonarr categories, 85.35 GiB free, and DHT idle behind the VPN](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S04-qBittorrent-WebUI-Baseline-Categories-2026-07-17.png)

### Step 5: Configure Jellyfin Quick Sync transcoding

**UI path and action:** In Jellyfin Dashboard > Playback > Transcoding, I selected Intel QuickSync, left the device field blank, enabled the researched decode formats and hardware encoding, disabled AV1 and both HEVC RExt profiles, preferred OS-native VA-API decoders, left both Intel Low-Power encoders off, allowed HEVC output, and saved.

**Observed result:** Jellyfin retained Intel QuickSync, hardware encoding, HEVC output, OS-native VA-API decoders, & the disabled AV1/HEVC RExt selections from my [media settings research](../Media%20Settings%20Research%20-%202026-07-17.md).

**Verification:** I reviewed the visible decode and encode selections after saving. The tone-mapping fields remain below the captured viewport and are tracked under deviations.

**Evidence:**

![Intel QuickSync transcoding with the researched decode and encode selections; tone-mapping fields sit below the captured viewport](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S05-Jellyfin-QSV-Transcoding-Settings-2026-07-17.png)

### Step 6: Configure Sonarr episode naming

**UI path and action:** In Sonarr > Settings > Media Management > Episode Naming, I enabled episode renaming, selected Smart Replace, kept `{Quality Full}` in the standard, daily, and anime formats, set season folders to `Season {season}`, and saved.

**Observed result:** Sonarr saved the naming configuration.

**Verification:** I reopened the media-management view and confirmed the retained values.

**Evidence:**

![Sonarr episode renaming with Smart Replace and Season {season} folders](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S06-Sonarr-Episode-Naming-2026-07-17.png)

### Step 7: Set the Sonarr television root folder

**UI path and action:** In Sonarr > Settings > Media Management > Root Folders, I added `/data/media/tv` as the television root folder.

**Observed result:** Sonarr reported 85.4 GiB free and zero unmapped folders.

**Verification:** The root-folder page showed `/data/media/tv` available with no mapping error.

**Evidence:**

![Sonarr television root folder /data/media/tv with 85.4 GiB free and zero unmapped folders](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S07-Sonarr-Root-Folder-TV-2026-07-17.png)

### Step 8: Verify Sonarr's qBittorrent connection

**UI path and action:** In Sonarr > Settings > Download Clients, I opened `qBittorrent via Proton VPN`, enabled the client and completed-download handling, enabled failed-download redownload for automatic and interactive searches, and saved.

**Observed result:** Sonarr retained the enabled client and handling settings with no remote path mappings.

**Verification:** I reviewed the download-client settings after saving.

**Evidence:**

![Sonarr qBittorrent via Proton VPN client enabled with completed-download handling and failed-download redownload on](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S08-Sonarr-Download-Client-Handling-2026-07-17.png)

### Step 9: Configure Radarr movie naming and imports

**UI path and action:** In Radarr > Settings > Media Management, I set the movie filename to `{Movie Title} ({Release Year}) {Quality Full}`, used the matching folder format, enabled hard-links instead of copy, set the minimum-free-space import guard to 100 MB, and saved.

**Observed result:** Radarr saved the naming and import settings.

**Verification:** I reopened the media-management view and confirmed the retained values.

**Evidence:**

![Radarr movie naming with hard-links-instead-of-copy enabled and a 100 MB minimum-free-space import guard](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S09-Radarr-Movie-Naming-Hardlinks-2026-07-17.png)

### Step 10: Set the Radarr movie root folder

**UI path and action:** In Radarr > Settings > Media Management > Root Folders, I added `/data/media/movies` as the movie root folder.

**Observed result:** Radarr reported 85.4 GiB free and zero unmapped folders.

**Verification:** The root-folder page showed `/data/media/movies` available with no mapping error.

**Evidence:**

![Radarr movie root folder /data/media/movies with 85.4 GiB free and zero unmapped folders](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S10-Radarr-Root-Folder-Movies-2026-07-17.png)

### Step 11: Review Radarr quality and delay profiles

**UI path and action:** In Radarr > Settings > Profiles, I reviewed the six stock quality profiles, the default delay profile, and the empty release-profile list.

**Observed result:** Radarr retained the stock profile set with the default delay profile.

**Verification:** The profiles page showed six quality profiles, one default delay profile, and no release profiles.

**Evidence:**

![Radarr six stock quality profiles with the default delay profile and no release profiles](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S11-Radarr-Quality-Delay-Profiles-2026-07-17.png)

### Step 12: Verify Radarr's qBittorrent client entry

**UI path and action:** In Radarr > Settings > Download Clients, I opened the qBittorrent entry and reviewed host `gluetun`, port 8080, and category `radarr`.

**Observed result:** Radarr reached qBittorrent at `gluetun:8080` through the `radarr` category. The [configuration reference](../../Configuration/README.md) covers the Docker-subnet path.

**Verification:** The saved client detail displayed host `gluetun`, port 8080, & category `radarr`.

**Evidence:**

![Radarr download-client entry pointing at host gluetun port 8080 with category radarr](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S12-Radarr-qBittorrent-Client-Detail-2026-07-17.png)

### Step 13: Add the first Prowlarr indexer

**UI path and action:** In Prowlarr > Indexers > Add Indexer, I added one public torrent indexer at priority 25 with the Standard sync profile. I left the `flaresolverr` tag unused because this indexer doesn't require challenge handling.

**Observed result:** At 20:55 the enabled indexer synced through the Sonarr & Radarr application links established during deployment.

**Verification:** Prowlarr showed the indexer enabled and associated with the Standard sync profile.

**Evidence:** S13 has no screenshot. The [evidence index](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Evidence-Index.md) records the gap.

### Step 14: Connect Seerr to Jellyfin

**UI path and action:** In Seerr Setup Wizard > Jellyfin, I signed in to Jellyfin, continued to Library Sync, and enabled the returned `Movies` and `TV Shows` libraries.

**Observed result:** Seerr listed both Jellyfin libraries and allowed them to be enabled.

**Verification:** The library-sync page displayed `Movies` & `TV Shows` selected.

**Evidence:**

![Seerr setup wizard signed in to Jellyfin with the Movies and TV Shows libraries synced and enabled](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S14-Seerr-Jellyfin-Library-Sync-2026-07-17.png)

### Step 15: Connect Seerr to Radarr

**UI path and action:** In Seerr Setup Wizard > Services > Radarr, I added Radarr as the default movie server with the HD-1080p profile, root `/data/media/movies`, and minimum availability Released.

**Observed result:** Seerr returned `connection established successfully` & retained Radarr as the default server.

**Verification:** I reviewed the saved Radarr connection state before continuing.

**Evidence:**

![Seerr Radarr connection established with Radarr as default server](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S15-Seerr-Radarr-Connection-Established-2026-07-17.png)

### Step 16: Connect Seerr to Sonarr

**UI path and action:** In Seerr Setup Wizard > Services > Sonarr, I added Sonarr as the default series server with HD-1080p for standard and anime series, root `/data/media/tv`, and season folders enabled.

**Observed result:** Seerr retained the standard and anime profile selections and the root folder.

**Verification:** I reviewed the saved Sonarr server settings before finishing the wizard.

**Evidence:**

![Seerr Sonarr default-server settings with HD-1080p for standard and anime series and season folders on](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S16-Seerr-Sonarr-Server-Settings-2026-07-17.png)

### Step 17: Confirm the migrated Seerr interface

**UI path and action:** I completed the Seerr setup wizard and opened Seerr > Discover.

**Observed result:** The request interface rendered populated movie and television metadata.

**Verification:** The Discover page displayed populated movie & television rows after the wizard completed.

**Evidence:**

![Migrated Seerr request UI rendering populated Discover metadata after wizard completion](../../Evidence/Media%20Stack%20Application%20Onboarding%20-%202026-07-17/Screenshots/S17-Seerr-Discover-Populated-2026-07-17.png)

## Configuration Deviations & Evidence Gaps

- The Sonarr naming formats keep the season folder as `Season {season}` and omit the `{Release Group}` token; my [media settings research](../Media%20Settings%20Research%20-%202026-07-17.md) recommends `Season {season:00}` and retaining the release group. At the 2026-07-21 end-to-end test the episode imported and hard-linked correctly under the current scheme, so I declined that refinement and kept `Season {season}` without the release group.
- Sonarr's advanced Importing section (hard-link toggle) and Jellyfin's tone-mapping selections sit below the captured viewports. Radarr's hard-link setting is confirmed enabled; I confirmed Sonarr hard-linking and GPU-active playback at the 2026-07-21 end-to-end test.
- The Jellyfin library folder pickers are collapsed in S02–S03; the Arr root folders and the Seerr library sync corroborate the `/data/media` paths indirectly.
- There is no post-sync Sonarr or Radarr indexer-health screenshot. My [Arr indexer health record](../Troubleshooting/Arr%20Indexer%20Health%20Findings%20-%202026-07-17.md) records the pre-onboarding warnings; the 2026-07-21 acquisition test ran through both applications without a separate indexer-health capture.

## End-to-End Acquisition Test

On 2026-07-21 I ran the bounded end-to-end test in full. I requested a television episode and a movie, watched both acquire through Prowlarr search and the qBittorrent client inside the VPN namespace, compared qBittorrent's Content list against the payload filter during the transfer, confirmed the Sonarr and Radarr hard-link imports, and confirmed GPU-active playback in Jellyfin. The acquisition path works end to end.

The one retained capture is the Jellyfin `Movies` library, kept local under `Evidence/Media Stack End-to-End Acquisition Test - 2026-07-21/` because it shows an acquired title. FlareSolverr is validated in use: an indexer that requires Cloudflare challenge handling now runs through it.

## Rollback

Every change is an application-level UI setting: I can revert individual selections in place (library removal in Jellyfin, indexer removal in Prowlarr, server removal in Seerr, per-setting reversion in the Arr applications) without touching Compose, images, or the VPN path. No infrastructure change occurred.
