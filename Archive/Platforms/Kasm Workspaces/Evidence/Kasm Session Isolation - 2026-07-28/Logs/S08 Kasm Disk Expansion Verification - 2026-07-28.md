# S08 Kasm Disk Expansion Verification

**Created:** 2026-07-28  
**Last updated:** 2026-07-28

**Captured:** 2026-07-28T18:59:27-04:00  
**Target:** `purple-server`, VM 122 `kasm-01`  
**Execution:** SSH Manager MCP to the Proxmox host; QEMU guest agent for guest commands  
**Working directory:** SSH Manager default

I verified the existing resize. I did not issue a disk, partition, or filesystem mutation.

## Proxmox Disk

```text
$ qm config 122 | grep '^scsi0:'
scsi0: ssd-lvm2:vm-122-disk-1,iothread=1,size=150G,ssd=1
```

Standard error was empty and the exit code was 0.

```text
$ pvesm status --storage ssd-lvm2
Name            Type     Status     Total (KiB)      Used (KiB) Available (KiB)        %
ssd-lvm2     lvmthin     active       239185920       112632649       126553270   47.09%
```

Standard error was empty and the exit code was 0.

```text
$ lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent ssd-lvm2
  LV               LSize  Data%  Meta%
  ssd-lvm2         228.11 47.53  2.17
  vm-122-cloudinit   0.00 9.38
  vm-122-disk-0      0.00 14.06
  vm-122-disk-1    150.00 72.28
```

Standard error was empty and the exit code was 0.

## Guest Partition and Filesystem

```text
$ qm guest exec 122 -- /usr/bin/lsblk --output NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
NAME     SIZE TYPE FSTYPE  MOUNTPOINTS
sda      150G disk
|-sda1   149G part ext4    /var/lib/containerd/tmpmounts/containerd-mount1019313473
|                          /var/lib/docker/plugins/cc120208900b47185253520139449bf608a747b9d7934998d9a1cda6380bedc0/propagated-mount
|                          /
|-sda14    4M part
|-sda15  106M part vfat    /boot/efi
`-sda16  913M part ext4    /boot
sr0        4M rom  iso9660
```

The guest command exit code was 0. Standard error was empty.

```text
$ qm guest exec 122 -- /bin/df -hT /
Filesystem     Type  Size  Used Avail Use% Mounted on
/dev/sda1      ext4  145G  101G   44G  70% /
```

The guest command exit code was 0. Standard error was empty.

## Kasm Storage Paths

```text
$ qm guest exec 122 -- /usr/bin/findmnt --target /opt/kasm --output TARGET,SOURCE,FSTYPE,AVAIL,USE%
TARGET SOURCE    FSTYPE AVAIL USE%
/      /dev/sda1 ext4   42.5G  71%
```

```text
$ qm guest exec 122 -- /usr/bin/docker info --format '{{.DockerRootDir}}'
/var/lib/docker
```

```text
$ qm guest exec 122 -- /usr/bin/findmnt --target /var/lib/docker --output TARGET,SOURCE,FSTYPE,AVAIL,USE%
TARGET SOURCE    FSTYPE AVAIL USE%
/      /dev/sda1 ext4   41.5G  71%
```

Each guest command exited 0 with empty standard error. The available-space values changed while Docker wrote to the filesystem.

## Kasm Health

```text
$ qm guest exec 122 -- /usr/bin/docker ps --format '{{.Names}}|{{.Status}}'
kasm_proxy|Up 2 minutes
kasm_rdp_https_gateway|Up About a minute (healthy)
kasm_agent|Up 2 minutes (healthy)
kasm_rdp_gateway|Up About a minute (healthy)
kasm_api|Up 2 minutes (healthy)
kasm_manager|Up 2 minutes (healthy)
kasm_guac|Up 2 minutes (healthy)
kasm_db|Up 2 minutes (healthy)
```

```text
$ qm guest exec 122 -- /usr/bin/curl --insecure --silent --show-error https://127.0.0.1/api/__healthcheck
{"ok": true}
```

Both guest commands exited 0 with empty standard error. `kasm_proxy` has no Docker health check by design; the other seven service containers reported healthy.
