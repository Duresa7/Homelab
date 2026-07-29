# S00 Snapshot and Disk Growth

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Capture time:** 2026-07-28 23:35:24 through 23:37:14 UTC  
**Target:** `purple_server`, VM 122 `kasm-01`  
**Mechanism:** SSH Manager MCP, root shell on `purple-server`; QEMU guest agent for commands inside VM 122

## Action

I took `pre-workspace-buildout-2026-07-28`, shut down VM 122, changed `scsi0` from 150 GiB to 200 GiB, started the VM, and checked the partition and ext4 filesystem.

```bash
set -euo pipefail
printf '=== PHASE 0 START UTC ===\n'; date -u --iso-8601=seconds
printf '=== PRECHECK ===\n'; qm status 122; qm config 122 | grep '^scsi0:'; lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent,vg_name | sed -n '1p;/ssd-lvm2 /p'
printf '=== SNAPSHOT ===\n'; qm snapshot 122 pre-workspace-buildout-2026-07-28
qm listsnapshot 122
printf '=== SHUTDOWN ===\n'; qm shutdown 122 --timeout 300
qm status 122
printf '=== RESIZE ===\n'; qm resize 122 scsi0 200G
qm config 122 | grep '^scsi0:'
printf '=== START ===\n'; qm start 122
for i in $(seq 1 60); do if qm guest cmd 122 ping >/dev/null 2>&1; then echo "guest-agent-ready attempt=$i"; break; fi; sleep 2; if [ "$i" -eq 60 ]; then echo 'guest agent did not become ready' >&2; exit 1; fi; done
printf '=== GROW PARTITION AND FILESYSTEM ===\n'; qm guest exec 122 --timeout 120 -- /bin/bash -c 'set -e; lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS; growpart /dev/sda 1; resize2fs /dev/sda1; df -h /'
printf '=== POSTCHECK ===\n'; qm status 122; qm config 122 | grep '^scsi0:'; lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent,vg_name | sed -n '1p;/ssd-lvm2 /p'; qm guest exec 122 --timeout 60 -- /bin/bash -c 'lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS; df -h /; docker ps --format "{{.Names}} {{.Status}}"'
printf '=== PHASE 0 END UTC ===\n'; date -u --iso-8601=seconds
```

The SSH Manager call returned success with shell exit code 0. The material stdout was:

```text
=== PHASE 0 START UTC ===
2026-07-28T23:35:24+00:00
=== PRECHECK ===
status: running
scsi0: ssd-lvm2:vm-122-disk-1,iothread=1,size=150G,ssd=1
LV         LSize  Data%  Meta%  VG
ssd-lvm2   228.11 50.47  2.27   ssd-lvm2
=== SNAPSHOT ===
freeze guest filesystem
snapshotting 'drive-scsi0' (ssd-lvm2:vm-122-disk-1)
WARNING: You have not turned on protection against thin pools running out of space.
WARNING: Set activation/thin_pool_autoextend_threshold below 100 to trigger automatic extension of thin pools before they get full.
Logical volume "snap_vm-122-disk-1_pre-workspace-buildout-2026-07-28" created.
WARNING: Sum of all thin volume sizes (<300.01 GiB) exceeds the size of thin pool ssd-lvm2/ssd-lvm2 and the size of whole volume group (232.88 GiB).
snapshotting 'drive-efidisk0' (ssd-lvm2:vm-122-disk-0)
Logical volume "snap_vm-122-disk-0_pre-workspace-buildout-2026-07-28" created.
thaw guest filesystem
`-> pre-workspace-buildout-2026-07-28 2026-07-28 19:35:27     no-description
 `-> current                                            You are here!
=== SHUTDOWN ===
status: stopped
=== RESIZE ===
Size of logical volume ssd-lvm2/vm-122-disk-1 changed from 150.00 GiB (38400 extents) to 200.00 GiB (51200 extents).
Logical volume ssd-lvm2/vm-122-disk-1 successfully resized.
WARNING: Sum of all thin volume sizes (350.01 GiB) exceeds the size of thin pool ssd-lvm2/ssd-lvm2 and the size of whole volume group (232.88 GiB).
scsi0: ssd-lvm2:vm-122-disk-1,iothread=1,size=200G,ssd=1
=== START ===
generating cloud-init ISO
guest-agent-ready attempt=3
=== GROW PARTITION AND FILESYSTEM ===
NAME     SIZE FSTYPE  MOUNTPOINTS
sda      200G
|-sda1   199G ext4    /
|-sda14    4M
|-sda15  106M vfat    /boot/efi
`-sda16  913M ext4    /boot
sr0        4M iso9660
NOCHANGE: partition 1 is size 417331167. it cannot be grown
guest exit code: 1
=== POSTCHECK ===
status: running
scsi0: ssd-lvm2:vm-122-disk-1,iothread=1,size=200G,ssd=1
LV         LSize  Data%  Meta%  VG
ssd-lvm2   228.11 50.56  2.31   ssd-lvm2
NAME     SIZE FSTYPE  MOUNTPOINTS
sda      200G
|-sda1   199G ext4    /
|-sda14    4M
|-sda15  106M vfat    /boot/efi
`-sda16  913M ext4    /boot
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       193G  117G   76G  61% /
=== PHASE 0 END UTC ===
2026-07-28T23:37:02+00:00
```

## Verification

Cloud-init grew the partition and filesystem during the first boot. That left `growpart` with nothing to change, so the chained command stopped before its explicit `resize2fs` call. I ran `resize2fs` alone to distinguish an already-grown filesystem from a failed resize:

```bash
set -euo pipefail
printf '=== PHASE 0 FILESYSTEM CONFIRMATION UTC ===\n'; date -u --iso-8601=seconds
qm guest exec 122 --timeout 120 -- /bin/bash -c 'set -e; resize2fs /dev/sda1; lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS; df -h /'
printf '=== THIN POOL AFTER FILESYSTEM CONFIRMATION ===\n'; lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent,vg_name | sed -n '1p;/ssd-lvm2 /p'
```

That call returned shell exit code 0:

```text
=== PHASE 0 FILESYSTEM CONFIRMATION UTC ===
2026-07-28T23:37:14+00:00
resize2fs 1.47.0 (5-Feb-2023)
The filesystem is already 52166395 (4k) blocks long. Nothing to do!
NAME     SIZE FSTYPE  MOUNTPOINTS
sda      200G
|-sda1   199G ext4    /
|-sda14    4M
|-sda15  106M vfat    /boot/efi
`-sda16  913M ext4    /boot
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       193G  117G   76G  61% /
=== THIN POOL AFTER FILESYSTEM CONFIRMATION ===
LV         LSize  Data%  Meta%  VG
ssd-lvm2   228.11 50.64  2.32   ssd-lvm2
```

The disk, partition, and ext4 filesystem all carry the new size. The thin pool stayed 34.36 percentage points below the plan's 85 percent stop condition.
