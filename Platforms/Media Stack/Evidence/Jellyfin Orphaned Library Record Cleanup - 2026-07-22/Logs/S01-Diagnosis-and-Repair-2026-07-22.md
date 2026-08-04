# S01 Jellyfin Orphaned Library Record Diagnosis and Repair

**Created:** 2026-07-22  
**Last updated:** 2026-08-04

**Capture window:** 2026-07-22 21:50 through 21:56 EDT  
**Target:** SSH Manager `red_server`, Proxmox CT 842 `media-01`  
**Mechanism:** SSH Manager `ssh_execute`; `pct exec 842 -- sh -lc`  
**Guest working directories:** `/opt/media-stack`, `/data/media`

I replaced the removed title and Jellyfin item IDs with contextual redaction markers. The administrator access token stayed in the remote variable `$jf_token`; it wasn't printed, copied into this transcript, or retained in a file.

## Filesystem and container check

```sh
docker inspect jellyfin --format 'User={{.Config.User}} Mounts={{range .Mounts}}{{.Destination}}:RW={{.RW}};{{end}}'
docker exec jellyfin sh -lc 'id; findmnt -T /media/tv'
stat -c '%A %a %u:%g %n' /data/media /data/media/tv
find '/data/media/tv/<REDACTED_TV_SERIES>' -maxdepth 3
docker exec --user 1000:1000 jellyfin sh -lc 'set -eu; p="/media/tv/.jellyfin-delete-probe-$$"; mkdir "$p"; printf test > "$p/probe"; rm "$p/probe"; rmdir "$p"; echo create_write_delete=passed'
find /data/media/tv -maxdepth 1 -name '.jellyfin-delete-probe-*' -print
```

```text
User=1000:1000
/media:RW=true
uid=1000 gid=1000 groups=1000
/media /dev/sda1[/data/media] ext4 rw,noatime
drwxr-xr-x 755 1000:1000 /data/media
drwxr-xr-x 755 1000:1000 /data/media/tv
find: '/data/media/tv/<REDACTED_TV_SERIES>': No such file or directory
create_write_delete=passed
(no leftover probe path)
```

The read-only inspection returned exit code `0`. The first combined probe returned exit code `1` when `stat` reached the absent series directory; I reran the write/delete test against the surviving TV root & it returned exit code `0`.

## Database and API reproduction

I queried `jellyfin.db` in SQLite read-only URI mode and selected only item identity, name, path, type, parent, folder, virtual-item, & refresh fields for the removed series subtree.

```text
matching_base_items=18
series=1
seasons=2
episodes=15
IsVirtualItem=0 for all 18 records
```

The authenticated request envelope was:

```sh
curl -sS -o /dev/null -w '%{http_code}\n' -H "X-Emby-Token: $jf_token" \
  'http://127.0.0.1:8096/Users/<REDACTED_ADMIN_USER_ID>/Items/<REDACTED_EPISODE_ITEM_ID>'
curl -sS -o /dev/null -w '%{http_code}\n' -X DELETE -H "X-Emby-Token: $jf_token" \
  'http://127.0.0.1:8096/Items/<REDACTED_EPISODE_ITEM_ID>'
```

```text
authenticated_user_item_get_http=200
delete_repro_http=404
[21:55:49] Error processing request: Could not find a part of the path '/media/tv/<REDACTED_TV_SERIES>/Season 2'. URL DELETE /Items/<REDACTED_EPISODE_ITEM_ID>.
matching_items_after_repro=18
```

Both curls completed normally; the printed HTTP status is the application result. The remote command returned exit code `0`.

## Correction

```sh
docker exec --user 1000:1000 jellyfin mkdir '/media/tv/<REDACTED_TV_SERIES>'
curl -sS -o /dev/null -w '%{http_code}\n' -X DELETE -H "X-Emby-Token: $jf_token" \
  'http://127.0.0.1:8096/Items/<REDACTED_SERIES_ITEM_ID>'
```

```text
series_delete_http=204
stale_directory_present=no
matching_items_after_fix=0
```

The combined correction & immediate verification returned exit code `0`. Jellyfin removed the empty directory itself; no cleanup command or backup followed it.

## Final verification

```sh
curl -sS -o /dev/null -w '%{http_code}\n' -X POST -H "X-Emby-Token: $jf_token" \
  http://127.0.0.1:8096/Library/Refresh
docker inspect -f '{{.State.Health.Status}}' jellyfin
cd /opt/media-stack && docker compose --profile vpn ps --format json
findmnt -T /data/media -no SOURCE,FSTYPE,OPTIONS
find /data/media/movies -type f | wc -l
find /data/media/tv -type f | wc -l
```

The database count & Sonarr state were read again after the scan. The Sonarr API key also stayed in a remote variable and wasn't printed.

```text
library_refresh_http=204
old_item_get_http=404
jellyfin_health=healthy
compose_services=8 running; Jellyfin and Gluetun healthy
media_mount=/dev/sda1[/data] ext4 rw,noatime
movie_file_count=24
tv_file_count=0
stale_path_present=no
stale_db_items=0
sonarr_original_series=id 3; monitored true; episodeFileCount 0
post_fix_path_errors=0
[21:56:44] Scan Media Library Completed after 0 minute(s) and 10 seconds
```

The final verification command returned exit code `0`.
