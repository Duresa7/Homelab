# Season Pack Stranded by Move Import

**Created:** 2026-10-27  
**Last updated:** 2026-10-27

**Troubleshooting date:** 2026-10-27  
**System:** Galaxy Proxmox cluster, `red-server`, CT 842 `media-01`  
**Status:** Resolved. All 14 episodes imported and the torrent removed. The cause is a consequence of not seeding, which I keep.

## Symptom

qBittorrent showed `[Grupa Mirai] Dragon Ball Super - BD Box 1-11 (001-131+SP) [1080p]` at 0% in the `missingFiles` state, with 0 seeders and 35 leechers on its trackers. Sonarr had grabbed it for Dragon Ball Super S01E01 through S01E14 and held 14 queue rows against it, each with:

```text
qBittorrent is reporting missing files
```

Thirteen of those episodes had no file in the library.

## What I Tried

qBittorrent's torrent record contradicted the 0%. `completion_on` was 7:22 AM on 2026-10-17, `downloaded` was 91,734,824,697 bytes against a 91,733,534,763-byte total, and 148 of the torrent's 149 files were on disk under `/data/downloads/complete` at their full sizes. The missing file was `[Grupa Mirai] Dragon Ball Super - 011 [BD 1080p AAC] [8A84DA16].mkv`, 582,332,860 bytes.

Sonarr's history held one import from the torrent, episode 011 at 7:23 AM on 2026-10-17, one minute after completion. The library copy of S01E11 had a link count of 1, and every file left in the download folder also had a link count of 1. Sonarr had moved 011 rather than hardlinked it, and had not imported any other file. The only log line it kept from that import was:

```text
2026-10-17 07:23:17.2|Warn|DownloadedEpisodesImportService|Non-sample file detected: [/data/downloads/complete/[Grupa Mirai] Dragon Ball Super - BD Box 1-11 (001-131+SP) [1080p]/[Grupa Mirai] Dragon Ball Super - 014 [BD 1080p AAC] [E9E18A0A].mkv]
```

That check belongs to Sonarr's cleanup of a source folder after a move import. The log kept nothing at a level that shows why the other 13 files were left out.

## Root Cause

qBittorrent's global share limit is ratio 0 with the stop action (`max_ratio_enabled=true`, `max_ratio=0`, `max_ratio_act=0`), so every torrent stops seeding the moment it completes. Sonarr hardlinks from a torrent that is still seeding and moves from one that has stopped. It treated the stopped torrent as finished and moved 011 out. With one file gone, qBittorrent flagged the whole torrent `missingFiles`, which it displays as 0%. Sonarr then waited on that state and never retried the rest of the pack.

A single-episode torrent survives this, because the one move is the whole import. A season pack that Sonarr imports only partly on its first pass is left stranded.

## Fix

I ran a Sonarr manual import of the 13 files for 001 to 010 and 012 to 014 in copy mode, mapping each file to its episode by absolute number, at `Bluray-1080p`, Japanese, release group `Grupa Mirai`, to match the existing 011. The first attempt carried the torrent's download ID. It failed with `System.NullReferenceException` in `ManualImportService.Execute`, but only after importing all 13 files. The second attempt, without the download ID, reported `Manually imported 13 files` and replaced those 13 with the same sources. Sonarr's Recycle Bin is empty, so nothing was left behind.

I then removed the 14 queue rows with `removeFromClient=true`, `blocklist=false` and `skipRedownload=true`, which deleted the torrent and its remaining 135 files.

For a while I replaced the ratio limit with a 60-minute seeding time, so torrents would still be seeding at import and Sonarr would hardlink. I reverted it before any torrent ran under it, because I don't seed. `qBittorrent.conf` again holds `Session\GlobalMaxRatio=0` and `Session\GlobalMaxSeedingMinutes=-1`.

## Verification

- All 14 of S01E01 to S01E14 have a library file, and the Season 1 folder holds exactly 14 `.mkv` files for them. The 13 new imports had a link count of 2 and shared an inode with their download file before the delete.
- After the delete, qBittorrent no longer lists the torrent, the download folder is gone, all 14 library files still exist at non-zero size, and Sonarr's queue holds no Dragon Ball Super row.
- `/data` went from 677G used (74%) to 598G used (66%).
- After the revert, qBittorrent's preferences returned `max_ratio_enabled=true`, `max_ratio=0`, `max_seeding_time_enabled=false` and `max_ratio_act=0`, and the forwarded port still matched `listen_port`.

## If It Happens Again

Not seeding means a season pack can strand again. The [runbook](../Runbook.md#season-pack-left-in-missingfiles) has the recovery steps.
