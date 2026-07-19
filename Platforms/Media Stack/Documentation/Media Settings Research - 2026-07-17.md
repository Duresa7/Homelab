# Media Settings Research

**Created:** 2026-07-17  
**Last updated:** 2026-07-18

## Purpose

This note records the exact Jellyfin 10.11.11 transcoding and Sonarr 4.0.19 media-management selections I chose for the deployed Media Stack. I combined what the first-party docs say with read-only checks of my running containers and Intel render device on 2026-07-17.

## Verified Platform Context

- The host processor is an Intel Core i5-8500T with Intel UHD Graphics 630 and Quick Sync Video. Intel lists UHD 630 and Quick Sync for this processor family in its product specifications [1].
- Jellyfin receives one Linux render node: `/dev/dri/renderD128`. The container uses Jellyfin 10.11.11, Jellyfin FFmpeg 7.1.4, and the Intel `iHD` media driver.
- The active driver advertises hardware decode for MPEG-2, H.264, VC-1, VP8, HEVC Main/Main 10, and VP9 Profile 0/Profile 2. It does not advertise AV1 or HEVC Range Extensions profiles.
- H.264 QSV and HEVC QSV hardware encoders are available. OpenCL initializes successfully against the UHD 630, while the host reports `HuC disabled`.
- Sonarr and qBittorrent each see the same `/data` mount. `/data/downloads`, `/data/media/tv`, and `/data/media/movies` are on the same filesystem, so this deployment can create hard links instead of duplicating torrent payloads.

Jellyfin recommends QSV on mainstream Intel GPUs under Linux and says to enable only codecs supported by the active device. It documents H.264 support on every QSV GPU, HEVC 8-bit on Gen 9 and newer, HEVC 10-bit on Gen 9.5 and newer, and AV1 decode only on Gen 12 and newer. UHD 630 is also listed in Jellyfin's mainstream performance tier [2].

## Jellyfin Transcoding Selections

I opened **Dashboard > Playback > Transcoding** and applied these settings:

| Setting | Selection | Reason |
|---|---|---|
| Hardware acceleration | **Intel Quick Sync (QSV)** | Jellyfin prefers QSV for supported mainstream Intel GPUs on Linux. |
| QSV Device | **Leave blank** | Only one render node is visible, and it is already the default `renderD128`. Jellyfin says to change the default render device only when necessary. If another render node is passed through later, explicitly select `/dev/dri/renderD128`. |
| H264 decode | **Enable** | Advertised by the active driver and supported by all QSV generations. |
| HEVC decode | **Enable** | Advertised as HEVC Main. |
| MPEG2 decode | **Enable** | Advertised by the active driver. |
| VC1 decode | **Enable** | Advertised by the active driver. |
| VP8 decode | **Enable** | Advertised by the active driver. |
| VP9 decode | **Enable** | Advertised as VP9 Profile 0. |
| AV1 decode | **Disable** | UHD 630 predates Gen 12 AV1 hardware decoding and the driver does not advertise AV1. |
| HEVC 10bit decode | **Enable** | Advertised as HEVC Main 10; Jellyfin documents support on Gen 9.5 and newer. |
| VP9 10bit decode | **Enable** | Advertised as VP9 Profile 2. |
| HEVC RExt 8/10bit decode | **Disable** | No HEVC Range Extensions profile is advertised. |
| HEVC RExt 12bit decode | **Disable** | No HEVC Range Extensions or 12-bit profile is advertised. |
| Prefer OS native DXVA or VA-API hardware decoders | **Enable** | This permits the QSV/VA-API hybrid path. Jellyfin states this option is required for Dolby Vision support. |
| Enable hardware encoding | **Enable** | Both `h264_qsv` and `hevc_qsv` are present in Jellyfin FFmpeg. |
| Intel Low-Power H.264 encoder | **Disable** | The host currently reports HuC disabled. Jellyfin says Low-Power encoding relies on HuC and should be enabled only after its documented host configuration and verification. |
| Intel Low-Power HEVC encoder | **Disable** | Jellyfin documents Gen 9.x Low-Power support as H.264-only; UHD 630 is a Gen 9.5 platform. |
| Allow encoding in HEVC format | **Enable** | HEVC QSV encoding is available. Jellyfin will still choose an output based on the requesting client's capabilities; H.264 output remains available for broader compatibility. |
| Allow encoding in AV1 format | **Disable** | UHD 630 has no AV1 hardware encoder. |

I trusted the live hardware profile over enabling every box shown by the UI. Jellyfin's hardware-acceleration overview also notes that unsupported stages fall back to partial or software acceleration [3].

### Tone Mapping

The UHD 630 supports HEVC 10-bit decode and the live OpenCL test succeeded, so HDR-to-SDR hardware tone mapping applies. Jellyfin documents hardware tone mapping on Intel GPUs with HEVC 10-bit decoding and says VPP is preferred when VPP and OpenCL tone mapping are both enabled.

I use these selections:

| Setting | Selection |
|---|---|
| Enable VPP tone mapping | **Disable** |
| VPP brightness gain | Leave unchanged; unused while VPP is disabled |
| VPP contrast gain | Leave unchanged; unused while VPP is disabled |
| Enable tone mapping | **Enable** as the OpenCL path and Dolby Vision-capable fallback |
| Tone-mapping algorithm | **BT.2390** |
| Tone-mapping mode | **Auto** |
| Tone-mapping range | **Auto** |
| Remaining tone-mapping controls | **Leave at Jellyfin defaults** until a real HDR-to-SDR test shows a specific image problem |

Jellyfin describes VPP as limited to certain Intel GPU models. Intel's current `iHD` media-driver feature matrix does not list fixed-function HDR10 tone mapping for the KBLx group, which includes Coffee Lake, so I keep VPP disabled on this host [4]. I chose the OpenCL path because the live QSV-to-OpenCL mapping test succeeded. The behavior and tradeoffs are in Jellyfin's Intel tone-mapping documentation [5]. After saving, I force one known H.264 transcode and one HEVC Main 10 HDR-to-SDR transcode by lowering client quality; Jellyfin's Linux verification procedure calls for checking actual GPU video-engine activity during playback [6].

## Sonarr Media Management Selections

The screenshot is in basic view: its top action says **Show Advanced**. The missing hard-link option is an advanced setting, not a removed Sonarr v4 feature. I click **Show Advanced**, stay on **Settings > Media Management**, scroll to **Importing**, and enable **Use Hardlinks instead of Copy**. Sonarr's current documentation says the option is under Importing, is enabled by default, requires the completed-download and library paths to be on the same filesystem, and falls back to copying when a hard link cannot be created [7][8].

This deployment satisfies the filesystem and container-path requirements because both applications receive `/data` as one mount. I use these selections:

| Setting | Selection |
|---|---|
| Rename Episodes | **Enable** |
| Replace Illegal Characters | **Enable** |
| Colon Replacement | **Smart Replace** |
| Standard Episode Format | `{Series Title} - S{season:00}E{episode:00} - {Episode Title} {Quality Full} {Release Group}` |
| Daily Episode Format | `{Series Title} - {Air-Date} - {Episode Title} {Quality Full} {Release Group}` |
| Anime Episode Format | `{Series Title} - S{season:00}E{episode:00} - {Episode Title} {Quality Full} {Release Group}` |
| Season Folder Format | `Season {season:00}` |
| Multi Episode Style | **Prefixed Range** |
| Use Hardlinks instead of Copy | **Enable** after clicking **Show Advanced** |

**Smart Replace** is the current Sonarr default: it replaces a colon followed by a space with a dash and otherwise removes the colon. That is appropriate for Linux and avoids characters Jellyfin identifies as problematic. Sonarr's Quick Start Guide recommends keeping quality/resolution and release-group information because omitted data cannot be recovered later [9]. Jellyfin recommends `Season 01`-style zero-padded season folders and `S01E01` episode identifiers in its TV show naming guide [10].

The formats above make only two material changes from the screenshot: add `{Release Group}` and pad the season folder to two digits. If I collect no anime, the anime format stays unused and needs no further tuning.

## Immediate Walkthrough Position

The screenshots and live read-only state show these steps are already complete:

- Jellyfin's initial wizard is complete.
- Jellyfin is already set to Intel QSV with a blank QSV Device, OS-native decoding enabled, hardware encoding enabled, and both Low-Power encoders disabled.
- Sonarr has the television root folder `/data/media/tv`.
- Sonarr episode renaming, illegal-character replacement, and Smart Replace are already enabled.

I continue from the current screens in this order:

1. In Jellyfin, add MPEG-2, VP8, VP9, HEVC 10-bit, and VP9 10-bit to the saved hardware-decoding list; leave AV1 and both HEVC RExt boxes off. Keep **QSV Device** blank, enable HEVC output and OpenCL tone mapping, leave VPP off, and save.
2. In Sonarr, click **Show Advanced**, add `{Release Group}` to the three naming formats, change the season format to `Season {season:00}`, enable **Use Hardlinks instead of Copy**, and save.
3. Finish the Jellyfin TV library using `/data/media/tv`; use content type **Shows**, leave embedded-title preferences disabled, and keep the library language and country selections appropriate for the collection.
4. Perform one bounded end-to-end episode import. Confirm that the imported library file and completed-download file are hard links to the same inode, then trigger a lower-quality Jellyfin playback and verify the GPU is active.

These instructions intentionally keep passwords, API keys, VPN material, and other secrets outside the repository.

## Sources

1. [Intel processor comparison, Core i5-8500T](https://www.intel.com/content/www/us/en/products/compare.html?productIds=129939%2C129941%2C135935%2C129944) - UHD 630 graphics and Quick Sync support for this processor family.
2. [Jellyfin Intel GPU transcoding guide](https://jellyfin.org/docs/general/post-install/transcoding/hardware-acceleration/intel/) - QSV preference on mainstream Intel GPUs and the codec-generation support matrix.
3. [Jellyfin hardware-acceleration overview](https://jellyfin.org/docs/general/post-install/transcoding/hardware-acceleration/) - fallback to partial or software acceleration for unsupported stages.
4. [Intel iHD media-driver video-processing feature matrix](https://github.com/intel/media-driver#video-processing-features) - absence of fixed-function HDR10 tone mapping for the KBLx (Coffee Lake) group.
5. [Jellyfin Intel tone-mapping methods](https://jellyfin.org/docs/general/post-install/transcoding/hardware-acceleration/intel/#tone-mapping-methods) - VPP-versus-OpenCL tone-mapping behavior and tradeoffs.
6. [Jellyfin Linux hardware-acceleration verification](https://jellyfin.org/docs/general/post-install/transcoding/hardware-acceleration/intel/#verify-on-linux) - checking GPU video-engine activity during playback.
7. [Sonarr Settings, Media Management](https://wiki.servarr.com/sonarr/settings#media-management) - hard-link option location, default state, and same-filesystem requirement.
8. [Servarr Docker Guide](https://wiki.servarr.com/docker-guide) - single-mount container path requirement for hard links.
9. [Sonarr Quick Start Guide, Media Management](https://wiki.servarr.com/sonarr/quick-start-guide#media-management) - retaining quality and release-group information in naming formats.
10. [Jellyfin TV show naming guide](https://jellyfin.org/docs/general/server/media/shows/) - zero-padded season folders and `S01E01` episode identifiers.
