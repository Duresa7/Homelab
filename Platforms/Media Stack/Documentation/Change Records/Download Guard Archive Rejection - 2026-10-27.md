# Download guard archive rejection

**Created:** 2026-10-27  
**Last updated:** 2026-10-27

The [download guard](Download%20Guard%20-%202026-10-11.md) let ten fake TV releases sit in qBittorrent on `media-01`. Each torrent was a single archive named after a real episode, and six of them held a Windows executable. Neither layer caught them: qBittorrent's excluded-name filter only sees the file names in the torrent, which ended in `.7z`, and the guard deliberately left any torrent holding an archive alone. Sonarr refused all ten with `Invalid video file, unsupported extension: '.7z'` and waited on them indefinitely, so the episodes never arrived.

I closed the gap in two places. Sonarr and Radarr now reject a release by title before it is grabbed, and the guard now rejects a torrent that holds archives and no video.

## What the fake releases were

All ten came from LimeTorrents through Prowlarr, for episodes of Marshals, Tulsa King, Avatar: Seven Havens, Dark Matter, VisionQuest and MobLand. Their titles copied real release groups and ended in a bare ` 7z`, for example `Marshals S02E04 Blast Radius 1080p WEB H264-CAKES 7z`. Six different episodes were byte-identical at 993,259,160 bytes and three more at 901,376,019 bytes.

Six of the files were ZIP archives under a `.7z` name. I listed them without extracting, and each held one entry, `vlc-3.0.23-win64_crypted.exe`, 1,023,025,653 bytes. The other four were real 7z archives that nothing on the host could list. `media-01` is a Linux container with no SMB or NFS listener, nothing in the stack unpacks archives, and Sonarr never imported them, so the executable had no path to run.

## Grab-time rejection

I added a custom format named **Archive or Executable Release** to Sonarr (ID 46) and Radarr (ID 4). It has one required `ReleaseTitleSpecification`:

```text
(?i)\b(7z|zip|rar|tar|exe|msi|scr|lnk|bat|cmd|ps1|vbs|js|apk)$
```

It scores -10000 in all nine Sonarr quality profiles and all six Radarr profiles. The highest minimum score among them is 10000 and the lowest is 0, so a matching release falls below every profile's minimum and is never grabbed.

Before creating it, I ran the expression against the grab history. It matched 10 of Sonarr's 410 grabs, which were exactly the ten fakes, and none of Radarr's 2.

## Download-time rejection

The guard's `classify` function now returns `archive_payload` for a torrent whose files include an archive (`.rar`, `.zip`, `.7z`, `.tar`, `.gz`, `.bz2`, `.xz`, or an `.r00`-style split volume) and no video. A torrent with any video file still passes, so a release with a stray `sample.zip` beside its `.mkv` is unaffected. Disc images stay in the video set and still pass. The rejection follows the same path as the other two reasons: stop, record, blocklist, delete and bounded replacement search. It needs no two-minute metadata grace, because a non-empty file list is already complete.

This catches a fake whose title no longer ends in an archive extension. The [payload-filtering research](../Download%20Payload%20Filtering%20Research%20-%202026-07-17.md) had already noted that this stack cannot import archives, so rejecting archive-only torrents costs nothing a working release needs.

I replaced the unit test that asserted `film.rar` plus `film.r00` is preserved with one asserting that video plus `sample.zip` is preserved. I added a test covering archive-only payloads, including the fake-release shape, and one confirming the rejection runs immediately and in blocklist-before-delete order.

## Verification

- The 19 unit tests passed on `ubuntu-dev`.
- The script at `/opt/media-stack/scripts/media-download-guard.py` is root-owned, mode 0700, and hashes to `0879a362f0914cf8801cc649a422edf35354831eb28172657d34b29229668dc2`, the same SHA-256 as the [repository copy](../../Scripts/media-download-guard.py).
- Sonarr's parse endpoint scored the fake title `Marshals S02E04 Blast Radius 1080p WEB H264 CAKES 7z` at -10000 with the new format, and the clean title `Marshals S02E04 Blast Radius 1080p WEB H264-CAKES` at 0 without it.
- A dry run flagged exactly the ten fakes as `archive_payload` and left the other torrent in the queue alone.
- At 11:48 PM Eastern on 2026-10-27 the timer run logged ten `rejected` events for `archive_payload`, each with `files_deleted: true` and `tracked: true`. Sonarr's blocklist held all ten LimeTorrents titles, qBittorrent no longer listed them, and `/data/downloads/complete` held no `.7z` or `.zip` file.
- Between 11:51 PM and 11:55 PM, Sonarr imported real `.mkv` releases for six of the ten episodes, from EZTV, 1337x and Knaben.
- Between 11:51 PM and 11:52 PM, the guard rejected four Knaben replacements for Tulsa King S04E03, Dark Matter S02E10, Avatar: Seven Havens S01E10 and MobLand S02E07 as `blocked_file_type`, which is a match against qBittorrent's excluded-name list. Their titles followed the fakes' pattern, with the full episode title and `H264-EZTV`, a site name used as a group. That is the pre-existing rule working; Knaben grabs were rejected the same way at 11:34 AM and 11:50 AM that day.

## Open

- The four episodes above still have no file. The guard retries each at most twice, 30 minutes apart.
- The guard logs a rejection's reason but not the file that caused it. I can't confirm from the journal that the four Knaben rejections held an executable rather than a shortcut such as a `.url` file.
- A torrent with a video file plus an archive still passes. Sonarr imports only the video and leaves the archive in `/data/downloads`, where nothing runs it.
- LimeTorrents stays enabled in Prowlarr. It supplied all ten fakes and 21 legitimate grabs, and both new layers now stop these releases.
