# Media Stack Refresh and Payload Filtering

**Created:** 2026-07-17  
**Last updated:** 2026-07-18

**Implementation date:** 2026-07-17  
**System:** Galaxy Proxmox cluster, `red-server`, CT 842 `media-01`  
**Status:** Complete; first acquisition/import inspection remains part of onboarding

## Scope

I refreshed every media-stack image from its configured `latest` tag, replaced the retired Jellyseerr image with its Seerr successor, and stopped ordinary executable and script payloads from being selected in newly added qBittorrent torrents.

## Starting State

- All eight Compose services already used mutable `latest` tags, but I had not reconciled the running containers against the registries during this task.
- Jellyseerr 2.7.3 used `fallenbagel/jellyseerr:latest` and reported that an update was available.
- Sonarr used LinuxServer build `4.0.19.2979-ls319`.
- qBittorrent 5.2.3 had `excluded_file_names_enabled=false`, an empty exclusion list, automatic command execution disabled, and an empty torrent queue.

## Decisions

1. **Migrate to Seerr rather than update the retired Jellyseerr image.** Seerr is the maintained successor and provides an in-place migration path using the existing `/app/config` data.
2. **Preserve the `jellyseerr` Compose service name and configuration directory.** I changed only the image and init behavior, which minimizes migration risk and preserves the existing database.
3. **Use qBittorrent's native excluded-file-name setting.** It applies before normal Sonarr/Radarr additions transfer payload files and avoids an additional scanning container on the constrained 100 GiB guest.
4. **Use the conservative 100-pattern baseline.** It covers common executable, installer, script, shortcut, macro-enabled document, driver, and loadable-library suffixes. I kept archives, subtitles, media containers, and disc images allowed to avoid breaking legitimate releases.
5. **Continue tracking `latest`.** This honors my deployment policy, while the observed semantic versions and image reconciliation make this a bounded point-in-time refresh rather than an assumption that the tag updates running containers automatically.

## Actions and Results

| Step | Action | Observed result | Evidence disposition |
| --- | --- | --- | --- |
| S01 | Created a protected pre-migration configuration backup | `/opt/media-stack/backups/seerr-migration-2026-07-17/pre-migration-config.tar.gz` exists with restricted access; a protected pre-migration Compose copy is beside it | I did not capture the backup contents because they contain application secrets |
| S02 | Changed the request image to `ghcr.io/seerr-team/seerr:latest`, added `init: true`, and ensured the existing config tree is owned by UID/GID 1000 | Compose validation passed and Seerr reused the existing `/app/config` data | Secret-free structure is represented by [`compose.example.yml`](../../Configuration/compose.example.yml) |
| S03 | Pulled all eight configured images and reconciled the complete `vpn` profile | Seerr and Sonarr were recreated from newer images; the other six services already matched the pulled image state | Final running versions and container state are in the [verification transcript](../../Evidence/Media%20Stack%20Refresh%20and%20Payload%20Filtering%20-%202026-07-17/Logs/S03-S05-Verification-2026-07-17.md) |
| S04 | Enabled qBittorrent's excluded-file-name option with the researched baseline | API returned `excluded_file_names_enabled=true` and exactly 100 patterns; automatic command execution remained disabled | Pattern rationale and exact list are in the [research record](../Download%20Payload%20Filtering%20Research%20-%202026-07-17.md); current state is in the [verification transcript](../../Evidence/Media%20Stack%20Refresh%20and%20Payload%20Filtering%20-%202026-07-17/Logs/S03-S05-Verification-2026-07-17.md) |
| S05 | Restarted qBittorrent and performed full post-change checks | Eight services running; Jellyfin and Gluetun healthy; Seerr current; all management HTTP checks passed; Sonarr and Radarr each reached qBittorrent's API; VPN exit lookup succeeded without retaining the exit address; qBittorrent port matched Proton's forwarded port; queue remained empty | [Verification transcript](../../Evidence/Media%20Stack%20Refresh%20and%20Payload%20Filtering%20-%202026-07-17/Logs/S03-S05-Verification-2026-07-17.md) |
| S05A | Added a stopped local-only torrent made from harmless one-byte placeholders | `.exe` and `.ps1` received priority `0`; `.mkv` and the intentionally allowed `.zip` received priority `1`; I removed the test torrent and temporary files | [Functional filter-test transcript](../../Evidence/Media%20Stack%20Refresh%20and%20Payload%20Filtering%20-%202026-07-17/Logs/S05A-Functional-Filter-Test-2026-07-17.md) |

I did not capture the exact implementation command stream for S01-S04 while those actions ran, so I rely on the protected rollback artifact, the secret-free resulting structure, and the complete S05/S05A post-change transcripts. In future bounded refreshes I start transcript capture before the first mutation.

## Resulting Versions

| Service | Running result after registry refresh |
| --- | --- |
| Jellyfin | 10.11.11 |
| Seerr | 3.3.0; `updateAvailable=false`, zero commits behind |
| Sonarr | 4.0.19.2979, LinuxServer `ls320` |
| Radarr | 6.3.0.10514, LinuxServer `ls311` |
| Prowlarr | 2.4.0.5397, LinuxServer `ls154` |
| FlareSolverr | 3.5.0 |
| qBittorrent | 5.2.3 / libtorrent 2.0.13, LinuxServer `ls468` |
| Gluetun | Current pulled rolling `latest` image; its release relationship is recorded in the [research record](../Download%20Payload%20Filtering%20Research%20-%202026-07-17.md) |

The upstream comparison in the research record confirms that each semantic application version matches the latest non-prerelease GitHub release available on the implementation date. `latest` remains a mutable registry pointer and does not eliminate the need for future pull, recreation, and verification cycles.

## Filter Behavior

qBittorrent treats the patterns as case-insensitive wildcards, one per line, and marks a matching file or folder as **Do not download** when a new torrent is added without explicit file priorities. Normal Sonarr and Radarr qBittorrent additions do not supply those priorities, so the global list applies.

This is filename filtering rather than content inspection. Renamed payloads, extensionless executables, and executable content inside an allowed archive can evade it. BitTorrent piece boundaries can also cause some bytes belonging to an excluded file to enter qBittorrent's unwanted-file storage. My stopped local test proved ordinary `.exe` and `.ps1` names are assigned Do not download priority, while Sonarr and Radarr still limit normal imports to recognized media. I will still inspect the first real acquisition before treating import and playback as fully validated.

## Rollback

1. For the request service, stop Seerr, restore `/opt/media-stack/config/jellyseerr` and the protected Compose copy from `/opt/media-stack/backups/seerr-migration-2026-07-17`, validate Compose, and start the complete `vpn` profile. I do not restore the retired image unless a Seerr-specific failure requires that bounded rollback.
2. For qBittorrent, use its WebUI or `/api/v2/app/setPreferences` to set `excluded_file_names_enabled=false`; do not hand-edit the INI while qBittorrent is running.
3. Re-run the service, VPN, forwarded-port, and qBittorrent preference checks after either rollback.

## Remaining Verification

- During the first actual Sonarr and Radarr acquisition, inspect qBittorrent's Content list and verify unexpected payloads have zero priority.
- Confirm the requested media hard-links into the library and plays in Jellyfin.
- Confirm the migrated Seerr UI retains its Jellyfin, Sonarr, and Radarr connections.
