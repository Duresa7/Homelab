# S03 Media Stack HDD Copy and Cutover

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Captured:** 2026-07-22T03:03:40-04:00 through 2026-07-22T03:09:47-04:00  
**Target:** `red-server`, CT 842 `media-01`  
**Execution:** SSH Manager `ssh_execute`; root shell; default working directory

## Stopped copy

```sh
set -euo pipefail
date --iso-8601=seconds
pct exec 842 -- sh -lc 'cd /opt/media-stack
docker compose --profile vpn stop --timeout 60
test -z "$(docker compose --profile vpn ps --status running -q)"
docker compose --profile vpn ps'
pct shutdown 842 --timeout 60
test "$(pct status 842)" = "status: stopped"
pct mount 842
MEDIA_ROOTFS=/var/lib/lxc/842/rootfs
MEDIA_SOURCE="$MEDIA_ROOTFS/data"
MEDIA_DEST=/mnt/bindmounts/media-01-hdd/data
test -d "$MEDIA_SOURCE"
test -d "$MEDIA_DEST"
test "$(find "$MEDIA_DEST" -mindepth 1 -print -quit | wc -l)" -eq 0
printf 'source-files=%s\n' "$(find "$MEDIA_SOURCE" -xdev -type f | wc -l)"
printf 'source-bytes=%s\n' "$(du -sx --block-size=1 "$MEDIA_SOURCE" | cut -f1)"
stat -c '%n|uid=%u|gid=%g|mode=%a|device=%d' "$MEDIA_SOURCE" "$MEDIA_DEST"
rsync -aHAXS --numeric-ids --info=stats2 "$MEDIA_SOURCE/" "$MEDIA_DEST/"
sync
printf 'destination-files=%s\n' "$(find "$MEDIA_DEST" -xdev -type f | wc -l)"
printf 'destination-bytes=%s\n' "$(du -sx --block-size=1 "$MEDIA_DEST" | cut -f1)"
stat -c '%n|uid=%u|gid=%g|mode=%a|device=%d' "$MEDIA_SOURCE" "$MEDIA_DEST"
```

```text
2026-07-22T03:03:40-04:00
NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS    PORTS
mounted CT 842 in '/var/lib/lxc/842/rootfs'
source-files=19
source-bytes=10615713792
/var/lib/lxc/842/rootfs/data|uid=101000|gid=101000|mode=755|device=64518
/mnt/bindmounts/media-01-hdd/data|uid=101000|gid=101000|mode=755|device=2049

Number of files: 31 (reg: 19, dir: 12)
Number of created files: 30 (reg: 19, dir: 11)
Number of deleted files: 0
Number of regular files transferred: 19
Total file size: 10,615,586,954 bytes
Total transferred file size: 10,615,586,954 bytes
Literal data: 10,615,586,954 bytes
Matched data: 0 bytes
File list size: 0
File list generation time: 0.001 seconds
File list transfer time: 0.000 seconds
Total bytes sent: 10,618,180,557
Total bytes received: 436

sent 10,618,180,557 bytes  received 436 bytes  130,284,429.36 bytes/sec
total size is 10,615,586,954  speedup is 1.00
destination-files=19
destination-bytes=10615681024
/var/lib/lxc/842/rootfs/data|uid=101000|gid=101000|mode=755|device=64518
/mnt/bindmounts/media-01-hdd/data|uid=101000|gid=101000|mode=755|device=2049
```

Standard error recorded each of the eight containers stopping cleanly. Exit code: `0`.

## Content and metadata comparison

I generated relative-path SHA-256 manifests for all 19 files, generated path/type/size/UID/GID/mode/link-count manifests, compared each pair with `cmp`, & ran `rsync -aHAXScn --delete --numeric-ids --itemize-changes`. The command exited only after both `cmp` checks passed & the dry-run output stayed empty.

```text
2026-07-22T03:06:02-04:00
files=19
logical-bytes=10615586954
source-content-manifest-sha256=14a63738f3871ccb6dffad205c7189d75077eb245a1991f94d3792a850d1d886
destination-content-manifest-sha256=14a63738f3871ccb6dffad205c7189d75077eb245a1991f94d3792a850d1d886
source-metadata-manifest-sha256=63fb8ecbf67f1949ee43aeafda9c316f7764422478f6a78f528a94607466fda2
destination-metadata-manifest-sha256=63fb8ecbf67f1949ee43aeafda9c316f7764422478f6a78f528a94607466fda2
rsync-checksum-dry-run-changes=0
```

Standard error was empty. Exit code: `0`.

## CT mount attachment and restart

I renamed the source to `/data.nvme-source`, recreated `/data`, unmounted the offline root volume, set `mp0`, started CT 842, & started the existing stopped containers with `docker compose start`.

```text
2026-07-22T03:09:47-04:00
/var/lib/lxc/842/rootfs/data|uid=101000|gid=101000|mode=755|device=64518
/var/lib/lxc/842/rootfs/data.nvme-source|uid=101000|gid=101000|mode=755|device=64518
/mnt/bindmounts/media-01-hdd/data|uid=101000|gid=101000|mode=755|device=2049
mp0: /mnt/bindmounts/media-01-hdd/data,mp=/data,backup=0
active
TARGET SOURCE           FSTYPE OPTIONS
/data  /dev/sda1[/data] ext4   rw,noatime
Filesystem                       Type  Size  Used Avail Use% Mounted on
/dev/mapper/pve-vm--842--disk--0 ext4   98G   19G   74G  21% /
/dev/sda1                        ext4  916G  9.9G  906G   2% /data
/dev/mapper/pve-vm--842--disk--0 ext4   98G   19G   74G  21% /
/data|uid=1000|gid=1000|mode=755|device=2049
/data/downloads|uid=1000|gid=1000|mode=755|device=2049
/data/media|uid=1000|gid=1000|mode=755|device=2049
/data/transcodes|uid=1000|gid=1000|mode=755|device=2049
/data.nvme-source|uid=1000|gid=1000|mode=755|device=64518
/opt/media-stack|uid=1000|gid=1000|mode=755|device=64518
```

Docker reported each existing container starting; Gluetun reached healthy before qBittorrent started. The final Compose table contained eight running services, with Jellyfin & Gluetun healthy. Exit code: `0`.
