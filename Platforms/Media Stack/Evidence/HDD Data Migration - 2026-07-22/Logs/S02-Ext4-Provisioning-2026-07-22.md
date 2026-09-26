# S02 Media Stack HDD Ext4 Provisioning

**Created:** 2026-07-22  
**Last updated:** 2026-08-04

**Captured:** 2026-07-22T03:01:35-04:00  
**Target:** `red-server`; `/dev/disk/by-id/ata-ST1000LM035-1RK172_<REDACTED_DRIVE_SERIAL>`  
**Execution:** SSH Manager `ssh_execute`; root shell; default working directory

## Command

```sh
set -euo pipefail
MEDIA_DISK=/dev/disk/by-id/ata-ST1000LM035-1RK172_<REDACTED_DRIVE_SERIAL>
MEDIA_PART=/dev/disk/by-id/ata-ST1000LM035-1RK172_<REDACTED_DRIVE_SERIAL>-part1
MEDIA_MOUNT=/mnt/bindmounts/media-01-hdd
date --iso-8601=seconds
test "$(readlink -f "$MEDIA_DISK")" = /dev/sda
test -z "$(lsblk -nr -o NAME "$MEDIA_DISK" | tail -n +2)"
test ! -e "$MEDIA_PART"
install -d -m 0755 "$MEDIA_MOUNT"
test ! -e "$MEDIA_MOUNT/data"
printf 'label: gpt\nunit: sectors\n\n2048,,L\n' | sfdisk --wipe always "$MEDIA_DISK"
udevadm settle
test "$(readlink -f "$MEDIA_PART")" = /dev/sda1
mkfs.ext4 -F -b 4096 -L media-01-data -m 0 "$MEDIA_PART"
MEDIA_UUID="$(blkid -s UUID -o value "$MEDIA_PART")"
test -n "$MEDIA_UUID"
test "$(grep -cF "$MEDIA_MOUNT" /etc/fstab)" -eq 0
printf '# CT 842 media-01 bulk data\nUUID=%s %s ext4 noatime,nofail,x-systemd.automount,x-systemd.device-timeout=10s 0 2\n' "$MEDIA_UUID" "$MEDIA_MOUNT" >> /etc/fstab
systemctl daemon-reload
mount "$MEDIA_MOUNT"
install -d -m 0755 -o 101000 -g 101000 "$MEDIA_MOUNT/data"
sync
printf 'uuid=%s\n' "$MEDIA_UUID"
lsblk -e 7 -o NAME,PATH,SIZE,TYPE,FSTYPE,FSVER,PTTYPE,PARTTYPENAME,MOUNTPOINTS,MODEL,SERIAL "$MEDIA_DISK"
findmnt -T "$MEDIA_MOUNT/data" -o TARGET,SOURCE,FSTYPE,OPTIONS
tune2fs -l "$MEDIA_PART" | grep -E 'Filesystem volume name|Filesystem UUID|Filesystem features|Block size|Reserved block count|Filesystem state'
stat -c '%n|uid=%u|gid=%g|mode=%a|device=%d' "$MEDIA_MOUNT" "$MEDIA_MOUNT/data"
grep -F "$MEDIA_MOUNT" /etc/fstab
```

## Standard output

```text
2026-07-22T03:01:35-04:00
Checking that no-one is using this disk right now ... OK

Disk /dev/disk/by-id/ata-ST1000LM035-1RK172_<REDACTED_DRIVE_SERIAL>: 931.51 GiB, 1000204886016 bytes, 1953525168 sectors
Disk model: ST1000LM035-1RK1
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 4096 bytes
I/O size (minimum/optimal): 4096 bytes / 4096 bytes
Disklabel type: gpt
Disk identifier: 28C6CF19-51F0-4823-89F3-D1CE0B4DB5B4

Old situation:

>>> Script header accepted.
>>> Script header accepted.
>>> Created a new GPT disklabel (GUID: 1DB4C87F-3A43-4CD8-A94F-9CD3B2E7C364).
/dev/disk/by-id/ata-ST1000LM035-1RK172_<REDACTED_DRIVE_SERIAL>-part1: Created a new partition 1 of type 'Linux filesystem' and of size 931.5 GiB.
/dev/disk/by-id/ata-ST1000LM035-1RK172_<REDACTED_DRIVE_SERIAL>-part2: Done.

New situation:
Disklabel type: gpt
Disk identifier: 1DB4C87F-3A43-4CD8-A94F-9CD3B2E7C364

Device                                                Start        End    Sectors   Size Type
/dev/disk/by-id/ata-ST1000LM035-1RK172_<REDACTED_DRIVE_SERIAL>-part1  2048 1953523711 1953521664 931.5G Linux filesystem

The partition table has been altered.
Calling ioctl() to re-read partition table.
Syncing disks.
Creating filesystem with 244190208 4k blocks and 61054976 inodes
Filesystem UUID: 289788f9-52a4-4e49-885b-000e8d565c8b
Superblock backups stored on blocks:
        32768, 98304, 163840, 229376, 294912, 819200, 884736, 1605632, 2654208,
        4096000, 7962624, 11239424, 20480000, 23887872, 71663616, 78675968,
        102400000, 214990848

Allocating group tables: done
Writing inode tables: done
Creating journal (262144 blocks): done
Writing superblocks and filesystem accounting information: done

uuid=289788f9-52a4-4e49-885b-000e8d565c8b
NAME   PATH        SIZE TYPE FSTYPE FSVER PTTYPE PARTTYPENAME     MOUNTPOINTS                  MODEL              SERIAL
sda    /dev/sda  931.5G disk              gpt                                                  ST1000LM035-1RK172 <REDACTED_DRIVE_SERIAL>
└─sda1 /dev/sda1 931.5G part ext4   1.0   gpt    Linux filesystem /mnt/bindmounts/media-01-hdd
TARGET                       SOURCE    FSTYPE OPTIONS
/mnt/bindmounts/media-01-hdd /dev/sda1 ext4   rw,noatime
Filesystem volume name:   media-01-data
Filesystem UUID:          289788f9-52a4-4e49-885b-000e8d565c8b
Filesystem features:      has_journal ext_attr resize_inode dir_index orphan_file filetype needs_recovery extent 64bit flex_bg metadata_csum_seed sparse_super large_file huge_file dir_nlink extra_isize metadata_csum orphan_present
Filesystem state:         clean
Reserved block count:     0
Block size:               4096
/mnt/bindmounts/media-01-hdd|uid=0|gid=0|mode=755|device=2049
/mnt/bindmounts/media-01-hdd/data|uid=101000|gid=101000|mode=755|device=2049
UUID=289788f9-52a4-4e49-885b-000e8d565c8b /mnt/bindmounts/media-01-hdd ext4 noatime,nofail,x-systemd.automount,x-systemd.device-timeout=10s 0 2
```

## Standard error and exit code

```text
mke2fs 1.47.2 (1-Jan-2025)
```

Exit code: `0`.
