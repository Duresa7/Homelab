# Download guard deployment

**Created:** 2026-10-11  
**Last updated:** 2026-10-11

I added a second layer behind qBittorrent's filename filter on `media-01`. The filter stops an executable inside a torrent from being downloaded, but the torrent itself stays in the queue, Sonarr or Radarr keeps waiting on it, and nothing searches for a replacement. The guard closes that gap: a root-owned Python script, run by a systemd timer every 30 seconds, rejects a torrent whose payload contains a blocked file type or no video at all, blocklists the release in the application that asked for it, deletes the torrent, and then asks that application to search again, a bounded number of times.

## What it does

The [script](../../Scripts/media-download-guard.py) reads qBittorrent's torrent list through `docker exec qbittorrent curl` against the Web API on `127.0.0.1:8080`, and reaches Sonarr on 8989 and Radarr on 7878 with the API key read from each application's `config.xml` at run time. No key is stored in the script, the units or the repository. It refuses to run at all if qBittorrent's **Excluded file names** option is off or no longer contains `*.exe`, so the first layer cannot silently disappear underneath it.

It only looks at torrents in the `tv-sonarr` and `radarr` categories. A torrent is rejected for one of two reasons:

| Reason | Rule |
| --- | --- |
| `blocked_file_type` | Any file carries a code suffix (`.exe`, `.msi`, `.bat`, `.ps1`, `.js`, `.lnk`, `.dll`, `.sh`, `.apk` and the rest of the script's list) or matches one of qBittorrent's excluded-name patterns |
| `no_video_payload` | Every file is text, image, subtitle or shortcut, and the torrent is more than two minutes old, so metadata has had time to arrive |

Archives, disc images and split `.r00`-style volumes are left alone, and so is any torrent with at least one video file, so an unknown format gets a human look rather than an automatic delete.

A rejection runs in a fixed order: stop the torrent, record it in `/var/lib/media-download-guard/state.json`, find the queue rows that reference its hash, remove each row with `blocklist=true` and `skipRedownload=true`, then delete the torrent. Files are deleted only when every path sits under `/data/downloads`, contains no `..` and crosses no symlink; otherwise the torrent is removed and the files stay for me to look at. If the torrent is not yet tracked in either queue, the guard leaves it stopped and retries for ten minutes before deleting it untracked.

The replacement search is the part that could run away, so it is bounded three ways: at most two searches per episode or movie, at least 30 minutes between them, and at most six searches across the whole guard in any 24 hours. A search is skipped when the item already has a file, is unmonitored, has not aired or is not yet available, or already sits in the queue. Attempts are reserved in the state file before the search command is sent, so a timed-out request still counts.

## Implementation

The script lives at `/opt/media-stack/scripts/media-download-guard.py`, root-owned with mode 0700. The [service](../../Configuration/media-download-guard.service) is a oneshot unit with `ProtectSystem=strict`, `ProtectHome=true`, `PrivateTmp=true`, `NoNewPrivileges=true`, a 180-second timeout and `/var/lib/media-download-guard` as its only writable path. The [timer](../../Configuration/media-download-guard.timer) starts it 90 seconds after boot and 30 seconds after each run ends. A flock on `/var/lib/media-download-guard/lock` makes an overlapping start a no-op. The state file holds the denied hashes, the replacement targets and the search timestamps, and is written through a temp file and `os.replace`.

I started the timer at 6:29:52 PM Eastern on 2026-10-11, after one manual run at 6:19 PM that recorded five `blocked_file_type` denials from the queue as it stood. The [unit tests](../../Tests/test-media-download-guard.py) cover the classifier, the path checks, the blocklist-before-delete order, the retry bounds and the state file, and run against a fake client without touching a host:

```sh
python3 -I "Platforms/Media Stack/Tests/test-media-download-guard.py"
```

## Verification

I read the live state through SSH Manager at 6:56 PM Eastern on 2026-10-11.

- `media-download-guard.timer` is enabled and active. The service's last run started and finished at 6:55:47 PM with `Result=success`, and the journal holds 102 completed runs since 6:29:52 PM with no failure and no `guard_error` event.
- The service and timer on the host hash to the same SHA-256 as the repository copies. The host script differs from the repository copy only by a trailing newline.
- `/var/lib/media-download-guard` is mode 0700 and holds `lock` and a 585-byte `state.json` with five denied hashes, no replacement targets and no searches. qBittorrent held zero torrents, so none of the five remains.
- qBittorrent's excluded-name filter is enabled and still carries `*.exe`, which is the precondition the guard checks on every run.
- The 17 unit tests passed on `ubuntu-dev`.

I did not stage a torrent with an executable to watch a rejection end to end. The five denials in the state file came from the manual run before the timer existed, and I did not retain that run's output.
