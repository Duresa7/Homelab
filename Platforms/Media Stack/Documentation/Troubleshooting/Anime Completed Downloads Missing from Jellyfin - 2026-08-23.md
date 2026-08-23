# Anime Completed Downloads Missing from Jellyfin

**Created:** 2026-08-23  
**Last updated:** 2026-08-23

**Troubleshooting date:** 2026-08-23  
**System:** Galaxy Proxmox cluster, `red-server`, CT 842 `media-01`  
**Status:** Resolved for the files the completed torrents contained. Twenty-nine monitored aired episodes still need releases.

## Symptom

Sonarr and qBittorrent showed the Mushoku Tensei downloads complete, but Jellyfin exposed only 15 Mushoku Tensei episodes. Sonarr's queue expanded the two completed torrents into 47 episode rows, which made the queue look like 47 downloaded episodes even though the payloads held 23 files in total.

Sonarr reported two import warnings:

```text
No files found are eligible for import in /data/downloads/complete/Mushoku Tensei S01 1080p Dual Audio BDRip 10 bits DD x265-EMBER
Partial season packs are not supported
```

## What I Tried

I compared Sonarr's episode database and queue with qBittorrent's torrent contents and the files under `/data/media/anime`. The Season 1 torrent contained only eleven files, S01E01 through S01E11, and Sonarr had already imported all eleven. Its source directory no longer existed, so the remaining qBittorrent item could not provide another episode.

The Season 2 Part 2 torrent held twelve complete files named `S02 P02 E01` through `S02 P02 E12`. Sonarr returned all twelve from its manual-import endpoint with Italian language and `WEBDL-1080p` quality, but rejected their partial-season naming. I also confirmed the first file contained one Italian AC3 audio stream and no English audio stream.

I first posted the mapped selections back to `/api/v3/manualimport`. That endpoint only reprocessed and validated the selections, so it returned the mappings without importing a file. I then submitted the validated file list through Sonarr's `ManualImport` command with automatic import mode, which is the execution step used by Sonarr's interactive-import workflow.

## Root Cause

qBittorrent's complete state described each torrent payload, not the completeness of the television season or series. The Season 1 torrent itself stopped at E11.

The second payload was complete, but its `S02 P02 E##` filenames represented the second half of Season 2 with numbering restarted at one. Sonarr does not infer that Part 2 E01 means S02E13 and rejected the pack rather than risk assigning twelve files to the wrong episodes.

Both completed torrent records remained after their download paths disappeared. Sonarr continued tracking those stale qBittorrent records and generated one warning queue row per associated episode.

## Fix

I mapped Part 2 E01 through E12 to S02E13 through S02E24 and submitted all twelve through Sonarr's manual-import command. Sonarr imported and renamed the files under `/data/media/anime/Mushoku Tensei - Jobless Reincarnation/Season 2`.

I removed the two stale completed download groups through Sonarr's bulk queue action with download-client removal enabled, blocklisting disabled, and redownload disabled. Their source files were already absent, so this removed the qBittorrent metadata and queue warnings without deleting an unimported payload. I then ran a Jellyfin library scan.

## Verification

- Sonarr completed the command with `Manually imported 12 files`.
- Sonarr reported `hasFile=true` for every episode from S02E13 through S02E24.
- The Mushoku Tensei media tree rose from 15 to 27 video files.
- Jellyfin completed its library scan and reported 27 Mushoku Tensei episodes and 35 episodes across the two Anime series.
- Sonarr's anime queue contained zero rows after the stale download groups were removed.
- The 12-file source directory contained zero videos after import, and each normalized Season 2 file existed in the Anime library.
- Sonarr reported 56 monitored aired Mushoku Tensei episodes: 27 imported and 29 missing. The missing set is 12 from Season 1, 12 from Season 2, and five from Season 3. None was present in the two completed torrent payloads.

I kept no separate evidence folder. I verified the live APIs, torrent contents, media streams, filesystem, and completed library scan during the troubleshooting session.
