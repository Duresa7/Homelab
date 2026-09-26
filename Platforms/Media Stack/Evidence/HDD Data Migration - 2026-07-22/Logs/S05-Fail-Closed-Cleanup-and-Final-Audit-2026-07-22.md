# S05 Media Stack HDD Fail-Closed Test, Cleanup, and Final Audit

**Created:** 2026-07-22  
**Last updated:** 2026-07-22

**Captured:** 2026-07-22T03:13:55-04:00 through 2026-07-22T03:15:51-04:00  
**Target:** `red-server`, CT 842 `media-01`  
**Execution:** SSH Manager `ssh_execute`; root shell; default working directory

## Verification wrapper correction

The first wrapper stopped all eight containers, stopped CT 842, & unmounted the HDD. It then exited `1` because this assertion ran under `set -e` while `findmnt` returned its expected no-match exit status:

```sh
test -z "$(findmnt -rn -T "$MEDIA_MOUNT" -o SOURCE)"
```

The follow-up inspection found CT 842 stopped, both systemd units inactive, the HDD unmounted, the mountpoint present, the `data` child absent, & `mp0` unchanged. No copy or configuration changed during the failed wrapper.

## Missing-disk startup and recovery

I resumed from that exact stopped state, captured the expected `pct start` failure, started the fstab-generated automount, triggered the mount by reading its `data` child, & restarted the guest and existing containers.

```text
2026-07-22T03:14:31-04:00
missing-mount-start-rc=255
run_buffer: 569 Script exited with status 2
lxc_init: 1037 Failed to run lxc.hook.pre-start for container "842"
__lxc_start: 2208 Failed to initialize container "842"
startup for container '842' failed
TARGET                       SOURCE    FSTYPE OPTIONS
/mnt/bindmounts/media-01-hdd systemd-1 autofs rw,relatime,fd=83,pgrp=1,timeout=0,minproto=5,maxproto=5,direct,pipe_ino=313909
/mnt/bindmounts/media-01-hdd /dev/sda1 ext4   rw,noatime
ActiveState=active
SubState=running
TARGET SOURCE           FSTYPE OPTIONS
/data  /dev/sda1[/data] ext4   rw,noatime
post-remount-services=8
post-remount-gluetun=healthy
post-remount-jellyfin=healthy
rollback-source=present
```

Exit code: `0`.

## NVMe source deletion

The deletion guard required the exact real path `/data.nvme-source`, rejected symlinks, required root device `64518`, required a different destination device `2049`, & compared the 19-file count and 10,615,586,954 logical bytes before calling `rm -rf --one-file-system`.

```text
2026-07-22T03:15:18-04:00
delete-target=/data.nvme-source
delete-files=19
delete-logical-bytes=10615586954
source-device=64518
destination-device=2049
nvme-source-removed=yes
Filesystem                       Type  Size  Used Avail Use% Mounted on
/dev/mapper/pve-vm--842--disk--0 ext4   98G  9.1G   84G  10% /
/dev/sda1                        ext4  916G  9.9G  906G   2% /data
126M   /opt/media-stack
```

Standard error was empty. Exit code: `0`.

## Final audit

```text
2026-07-22T03:15:51-04:00
red-server
status: running
mp0: /mnt/bindmounts/media-01-hdd/data,mp=/data,backup=0
UUID=289788f9-52a4-4e49-885b-000e8d565c8b /mnt/bindmounts/media-01-hdd ext4 noatime,nofail,x-systemd.automount,x-systemd.device-timeout=10s 0 2
mount-unit=active/mounted
automount-unit=active/running
SMART overall-health self-assessment test result: PASSED
Reallocated_Sector_Ct=0
Reported_Uncorrect=0
Current_Pending_Sector=0
Offline_Uncorrectable=0
UDMA_CRC_Error_Count=0
files=19
logical-bytes=10615586954
services=8
gluetun=healthy
jellyfin=healthy
qbit-network-mode-match=yes
forwarded-port-match=yes
nvme-source=absent
temporary-files=absent
TARGET SOURCE           FSTYPE OPTIONS
/data  /dev/sda1[/data] ext4   rw,noatime
Filesystem                       Type  Size  Used Avail Use% Mounted on
/dev/mapper/pve-vm--842--disk--0 ext4   98G  9.1G   84G  10% /
/dev/sda1                        ext4  916G  9.9G  906G   2% /data
```

Standard error was empty. Exit code: `0`.
