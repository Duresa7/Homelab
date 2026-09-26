# S04 Media Stack HDD Functional Validation

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Captured:** 2026-07-22T03:12:27-04:00 through 2026-07-22T03:13:05-04:00  
**Target:** `red-server`, CT 842 `media-01`  
**Execution:** SSH Manager `ssh_execute`; root shell; default working directory

## Runtime and write-path checks

The assertion command checked eight Compose services, Jellyfin & Gluetun health, qBittorrent's container namespace, forwarded-port equality, different host and VPN organizations, six HTTP listeners, a qBittorrent write, a cross-tree hard link, mount capacity, ownership, & device numbers.

```text
2026-07-22T03:12:27-04:00
download-write|device=2049|uid=1000|gid=1000|bytes=14
hardlink|source-device=2049|target-device=2049|source-inode=37224480|target-inode=37224480|links=2
services=8
jellyfin-health=healthy
gluetun-health=healthy
qbit-network-mode-match=yes
forwarded-port-match=yes
vpn-egress-differs=yes
http-listeners=6
Filesystem                       Type  Size  Used Avail Use% Mounted on
/dev/mapper/pve-vm--842--disk--0 ext4   98G   19G   74G  21% /
/dev/sda1                        ext4  916G  9.9G  906G   2% /data
/dev/mapper/pve-vm--842--disk--0 ext4   98G   19G   74G  21% /
/data|device=2049|uid=1000|gid=1000|mode=755
/data/downloads|device=2049|uid=1000|gid=1000|mode=755
/data/media|device=2049|uid=1000|gid=1000|mode=755
/data/transcodes|device=2049|uid=1000|gid=1000|mode=755
/opt/media-stack|device=64518|uid=1000|gid=1000|mode=755
/opt/media-stack/config|device=64518|uid=1000|gid=1000|mode=755
/opt/media-stack/cache|device=64518|uid=1000|gid=1000|mode=755
```

Standard error was empty. Exit code: `0`. The command removed both temporary files before returning.

## Existing-media and Quick Sync check

I selected the first existing MKV or MP4 without printing its title, read its first video stream with Jellyfin's `ffprobe`, & encoded 10 seconds through `h264_qsv`. The command initialized QSV through `/dev/dri/renderD128` and wrote the output to `/transcodes/.migration-qsv-test.mp4`.

```text
2026-07-22T03:13:05-04:00
input-readable=yes
qsv-encoder=h264_qsv
output-codec=h264
transcode-output|device=2049|uid=1000|gid=1000|bytes=3187149
transcode-cleanup=passed
```

```text
libva info: VA-API version 1.23.0
libva info: Trying to open /usr/lib/jellyfin-ffmpeg/lib/dri/iHD_drv_video.so
libva info: Found init function __vaDriverInit_1_23
libva info: va_openDriver() returns 0
```

Exit code: `0`.
