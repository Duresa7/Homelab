# Download Payload Filtering Research

**Created:** 2026-07-17  
**Last updated:** 2026-07-17

## Recommendation

Enable qBittorrent's **Excluded file names** option and apply the baseline patterns below. This is the earliest useful built-in control in this stack: qBittorrent assigns matching payloads **Do not download** priority before a newly added torrent starts transferring. Keep Sonarr and Radarr's existing completed-download handling enabled as a second import-time check.

This is defense in depth, not antivirus. qBittorrent matches names, not file contents, and Sonarr/Radarr decide what to import rather than preventing every unwanted byte from reaching the download directory.

## Live Baseline

The initial read-only inspection on 2026-07-17, before the coordinating implementation applied the control, found:

- qBittorrent `5.2.3` is running.
- `excluded_file_names_enabled` was `false` and `excluded_file_names` was empty.
- The qBittorrent queue contains zero torrents, so enabling the setting now avoids a mixed old/new queue.
- Sonarr `4.0.19.2979` and Radarr `6.3.0.10514` add downloads through qBittorrent's API without supplying explicit per-file priorities.

The coordinating implementation subsequently enabled the setting with the 100 executable, script, and macro patterns below while the queue remained empty. A follow-up API read confirmed `excluded_file_names_enabled=true`, 100 returned patterns, and zero torrents. That mutation was not performed by this research subtask. The retained result is in [S03-S05 Verification - 2026-07-17](../Evidence/Media%20Stack%20Refresh%20and%20Payload%20Filtering%20-%202026-07-17/Logs/S03-S05-Verification-2026-07-17.md); re-read the live API before relying on it for a later change.

## Exact qBittorrent 5.2.3 Semantics

The WebUI field is under **Tools > Options > Downloads > Excluded file names**. Enable the checkbox and enter one wildcard pattern per line. The qBittorrent 5.2.3 UI documents these operators:

- `*` matches zero or more characters.
- `?` matches one character.
- `[...]` matches a character set or range.
- Matching is case-insensitive, so `*.exe` also matches an uppercase `.EXE` suffix.

The 5.2.3 implementation converts each line from wildcard syntax to an anchored regular expression, walks each path from the leaf file through its parent folders, and changes matching entries to `Ignored`/Do not download. Therefore, these are wildcard patterns rather than raw regular expressions, and a matching folder name also excludes its children. See the tagged [qBittorrent 5.2.3 option text](https://github.com/qbittorrent/qBittorrent/blob/0b63c3d17373f6132ea211c9dcd4241284ccdfaf/src/gui/optionsdialog.ui#L1550-L1577) and [matching implementation](https://github.com/qbittorrent/qBittorrent/blob/0b63c3d17373f6132ea211c9dcd4241284ccdfaf/src/base/bittorrent/sessionimpl.cpp#L4089-L4166).

The Web API exposes the same setting as:

- `excluded_file_names_enabled`: Boolean
- `excluded_file_names`: newline-delimited string

qBittorrent reads and writes those values through `/api/v2/app/preferences` and `/api/v2/app/setPreferences`. The setter is an HTTP `POST` whose form field named `json` contains a JSON object; it is not a raw JSON request body. That object may contain only the two keys being changed, with `excluded_file_names_enabled` as a Boolean and `excluded_file_names` as one string containing newline-separated patterns. See its [5.2.3 application-controller source](https://github.com/qbittorrent/qBittorrent/blob/0b63c3d17373f6132ea211c9dcd4241284ccdfaf/src/webui/api/appcontroller.cpp#L207-L215), [preference setter](https://github.com/qbittorrent/qBittorrent/blob/0b63c3d17373f6132ea211c9dcd4241284ccdfaf/src/webui/api/appcontroller.cpp#L666-L674), and [official Web API preference method](https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-%28qBittorrent-4.1%29#set-application-preferences). Prefer the WebUI or API over editing the live configuration file by hand.

The corresponding `qBittorrent.conf` representation is `[BitTorrent]` followed by `ExcludedFileNamesEnabled=true` and `Session\ExcludedFileNames=` with Qt's comma-separated list. The API represents the same list as newline-delimited text. qBittorrent constructs those keys in the tagged [session settings source](https://github.com/qbittorrent/qBittorrent/blob/0b63c3d17373f6132ea211c9dcd4241284ccdfaf/src/base/bittorrent/sessionimpl.cpp#L438-L439) and [setting declarations](https://github.com/qbittorrent/qBittorrent/blob/0b63c3d17373f6132ea211c9dcd4241284ccdfaf/src/base/bittorrent/sessionimpl.cpp#L560-L572). Stop qBittorrent before any manual INI edit because QSettings serialization and normal shutdown can overwrite external changes; use the WebUI or API instead.

### Recommended Baseline Patterns

Use this low-false-positive list for a television-and-movie-only download directory:

```text
*.ade
*.adp
*.apk
*.app
*.appimage
*.appinstaller
*.application
*.appref-ms
*.appx
*.appxbundle
*.bat
*.cgi
*.chm
*.cmd
*.com
*.command
*.cpl
*.csh
*.deb
*.desktop
*.dll
*.dmg
*.docm
*.dotm
*.dylib
*.drv
*.elf
*.exe
*.fish
*.gadget
*.hta
*.inf
*.ins
*.isp
*.jar
*.js
*.jse
*.ko
*.ksh
*.lnk
*.mde
*.mjs
*.msc
*.msh
*.msh1
*.msh1xml
*.msh2
*.msh2xml
*.mshxml
*.msi
*.msix
*.msixbundle
*.msp
*.mst
*.ocx
*.pif
*.pkg
*.pl
*.potm
*.ppsm
*.pptm
*.ps1
*.ps1xml
*.ps2
*.ps2xml
*.psc1
*.psc2
*.psd1
*.psm1
*.py
*.pyw
*.rb
*.reg
*.rpm
*.run
*.scf
*.scr
*.sct
*.sh
*.shb
*.shs
*.sldm
*.so
*.sys
*.url
*.vb
*.vbe
*.vbs
*.vxd
*.ws
*.wsc
*.wsf
*.wsh
*.xbap
*.xla
*.xlam
*.xlsm
*.xltm
*.xll
*.zsh
```

This baseline blocks common Windows, Linux, and macOS programs, installers, scripts, shortcuts, kernel modules, loadable libraries, and macro-enabled office documents without blocking ordinary media, subtitle, metadata, image, or audio suffixes. It is the exact 100-pattern list applied to the live qBittorrent instance on 2026-07-17.

For a stricter media-only posture, add common archive suffixes:

```text
*.7z
*.arj
*.bz2
*.gz
*.lzh
*.r[0-9][0-9]
*.rar
*.tar
*.tar.bz2
*.tar.gz
*.tb2
*.tbz2
*.tgz
*.txz
*.xz
*.zip
*.zipx
```

This stack has no archive-unpacking service and Sonarr/Radarr do not import archives as playable media, so blocking them is compatible with direct media-file releases. It will intentionally reject releases distributed as RAR or another archive, and may also reject ancillary subtitle archives. Retain the baseline alone if avoiding those false positives matters more than blocking normally named archives.

If disc-image media is not wanted, add this stricter optional group:

```text
*.bin
*.img
*.iso
*.nrg
*.vhd
*.vhdx
```

Those six are omitted from the baseline because Sonarr and Radarr recognize some of them as legitimate disc-media formats. Adding them intentionally trades disc-image compatibility for a narrower accepted payload set; see Sonarr's [media-extension list](https://github.com/Sonarr/Sonarr/blob/4ff1b780010d3d9ec76a4864dce96b6494e9caea/src/NzbDrone.Core/MediaFiles/MediaFileExtensions.cs) and Radarr's [media-extension list](https://github.com/Radarr/Radarr/blob/7827e5368947f158ad06f757334f5cde6c406411/src/NzbDrone.Core/MediaFiles/MediaFileExtensions.cs).

## Scope and Bypass Conditions

The filter is applied while a torrent is added when the caller did not explicitly supply file priorities, and again when a magnet receives its metadata. Changing the preference only rebuilds qBittorrent's pattern list; it does not iterate through already loaded torrents and rewrite their priorities. Apply the filter before adding new work, and audit any pre-existing torrent manually. The relevant add path is in qBittorrent's [5.2.3 session implementation](https://github.com/qbittorrent/qBittorrent/blob/0b63c3d17373f6132ea211c9dcd4241284ccdfaf/src/base/bittorrent/sessionimpl.cpp#L2838-L2851), while magnet metadata handling is in [TorrentImpl](https://github.com/qbittorrent/qBittorrent/blob/0b63c3d17373f6132ea211c9dcd4241284ccdfaf/src/base/bittorrent/torrentimpl.cpp#L1823-L1862).

The deployed Sonarr and Radarr versions submit a URL or torrent file, category, start state, and optional queue/layout controls, but not qBittorrent's `filePriorities` parameter. Their normal additions therefore receive qBittorrent's global exclusion filter. See the tagged [Sonarr qBittorrent proxy](https://github.com/Sonarr/Sonarr/blob/4ff1b780010d3d9ec76a4864dce96b6494e9caea/src/NzbDrone.Core/Download/Clients/QBittorrent/QBittorrentProxyV2.cs#L145-L181) and [Radarr qBittorrent proxy](https://github.com/Radarr/Radarr/blob/7827e5368947f158ad06f757334f5cde6c406411/src/NzbDrone.Core/Download/Clients/QBittorrent/QBittorrentProxyV2.cs#L145-L181).

Known limitations:

- A program renamed with an allowed media suffix, an executable without a suffix, or an archive renamed with an innocuous suffix can bypass a filename deny list.
- Archive contents are not inspected. Blocking common archive suffixes prevents the normal case but cannot identify an archive solely from its bytes.
- BitTorrent transfers pieces rather than independent files. A piece may span a selected and an excluded file, so some excluded bytes can still be downloaded and may appear in qBittorrent's unwanted-file storage. qBittorrent documents this in its [official FAQ](https://github.com/qbittorrent/qBittorrent/wiki/Frequently-Asked-Questions#i-configured-qbittorrent-to-not-download-some-files-in-a-torrent-but-they-still-appear-on-my-hard-disk-why-is-that).
- A client or operator that explicitly sets per-file priorities can bypass the filter for a known-metadata add. The normal Sonarr/Radarr integration does not currently do this.
- This control does not examine a media container for malformed or hostile codec data and does not replace keeping Jellyfin and its codec libraries current.

## Sonarr and Radarr Import Behavior

Sonarr and Radarr do not expose a general user-maintained extension blocklist for completed downloads. Their internal import code has three relevant behaviors:

1. Library scans and normal imports select files from a fixed list of recognized media extensions.
2. Direct-file imports reject built-in dangerous extensions (`.arj`, `.lnk`, `.lzh`, `.ps1`, `.scr`, `.vbs`, `.zipx`) and executable extensions (`.bat`, `.cmd`, `.exe`, `.sh`).
3. If a completed folder contains no importable video, the empty-result check reports dangerous, executable, or archive content. If valid video is also present, unrelated payloads are not copied into the media library, but they can remain in the completed-download directory while the torrent seeds.

The authoritative lists and checks are in Sonarr's [FileExtensions](https://github.com/Sonarr/Sonarr/blob/4ff1b780010d3d9ec76a4864dce96b6494e9caea/src/NzbDrone.Core/MediaFiles/FileExtensions.cs), [download import](https://github.com/Sonarr/Sonarr/blob/4ff1b780010d3d9ec76a4864dce96b6494e9caea/src/NzbDrone.Core/MediaFiles/DownloadedEpisodesImportService.cs#L251-L307), and [empty-result check](https://github.com/Sonarr/Sonarr/blob/4ff1b780010d3d9ec76a4864dce96b6494e9caea/src/NzbDrone.Core/MediaFiles/DownloadedEpisodesImportService.cs#L337-L356), with equivalent Radarr behavior in [FileExtensions](https://github.com/Radarr/Radarr/blob/7827e5368947f158ad06f757334f5cde6c406411/src/NzbDrone.Core/MediaFiles/FileExtensions.cs) and [DownloadedMovieImportService](https://github.com/Radarr/Radarr/blob/7827e5368947f158ad06f757334f5cde6c406411/src/NzbDrone.Core/MediaFiles/DownloadedMovieImportService.cs#L268-L373).

The Arr checks are useful import protection, but qBittorrent's earlier exclusion is still worthwhile because it keeps ordinary executable/script payloads out of their named download paths before import.

## Verification

The implementation completed a local-only functional check without joining a public swarm or using executable content:

1. The preferences API returned `excluded_file_names_enabled=true` and the exact 100-pattern count after a qBittorrent restart.
2. A stopped test torrent was created from one-byte placeholders named `sample-video.mkv`, `blocked-test.exe`, `blocked-test.ps1`, and `allowed-archive.zip`.
3. `/api/v2/torrents/files` returned priority `0`/Do not download for `.exe` and `.ps1`, while `.mkv` and the intentionally allowed `.zip` retained normal priority `1`.
4. The test torrent and temporary source files were deleted, and a follow-up query confirmed the torrent was absent.

The exact commands and results are retained in the [functional filter-test transcript](../Evidence/Media%20Stack%20Refresh%20and%20Payload%20Filtering%20-%202026-07-17/Logs/S05A-Functional-Filter-Test-2026-07-17.md).

Sonarr and Radarr were not given a real acquisition during this change because no indexers are configured. During the first real acquisition, inspect qBittorrent's Content list before completion and verify only the intended media hard-links into the library. Because the queue was empty before the change, no retroactive audit was required.

## Current Upstream Release Check

The live stack was compared with the latest non-prerelease GitHub releases on 2026-07-17:

| Service | Current upstream release | Live result |
|---|---|---|
| Jellyfin | [`v10.11.11`](https://github.com/jellyfin/jellyfin/releases/tag/v10.11.11) | `10.11.11`; current |
| Seerr, formerly Jellyseerr | [`v3.3.0`](https://github.com/seerr-team/seerr/releases/tag/v3.3.0) | `3.3.0`; current after migration to `ghcr.io/seerr-team/seerr` |
| Sonarr | [`v4.0.19.2979`](https://github.com/Sonarr/Sonarr/releases/tag/v4.0.19.2979) | `4.0.19.2979`; current |
| Radarr | [`v6.3.0.10514`](https://github.com/Radarr/Radarr/releases/tag/v6.3.0.10514) | `6.3.0.10514`; current |
| Prowlarr | [`v2.4.0.5397`](https://github.com/Prowlarr/Prowlarr/releases/tag/v2.4.0.5397) | `2.4.0.5397`; current |
| qBittorrent | [`release-5.2.3`](https://github.com/qbittorrent/qBittorrent/releases/tag/release-5.2.3) | `5.2.3`; current |
| Gluetun | [`v3.41.1`](https://github.com/passteque/gluetun/releases/tag/v3.41.1) | The `latest` image reports rolling commit `93cc5a4`; it is newer than the tagged stable release but does not expose a comparable semantic version |
| FlareSolverr | [`v3.5.0`](https://github.com/FlareSolverr/FlareSolverr/releases/tag/v3.5.0) | `3.5.0`; current |

Every Compose service currently uses a mutable `latest` image tag. A running container does not replace itself when a registry moves that tag. Docker Compose documents that `latest` is pulled when the service is created under the default `missing` policy, and `docker compose pull` explicitly refreshes the local image; recreation is still required to run the newly pulled digest. See Docker's [Compose pull-policy reference](https://docs.docker.com/reference/compose-file/services/#pull_policy), [`docker compose pull`](https://docs.docker.com/reference/cli/docker/compose/pull/), and [`docker compose up`](https://docs.docker.com/reference/cli/docker/compose/up/).

For repeatable upgrades, record and verify the running application versions after each pull/recreation. Treat `latest` as a moving registry pointer, not a version assertion.
