# S05 Final Baseline Removal

**Created:** 2026-07-29  
**Last updated:** 2026-07-30

**Incident:** [Kasm Workspaces Thin Pool Exhaustion](../../../Thin%20Pool%20Exhaustion%20-%202026-07-29.md)

## Capture

- Capture time: 2026-07-29 23:56 through 23:57 EDT
- Proxmox target: `purple-server`
- Guest target: `kasm-01`, VM 122
- Remote mechanism: SSH Manager MCP to a Bash shell on `purple-server`
- Local verification mechanism: Windows PowerShell with `curl.exe`

## Step 1: Verify the final snapshot

I verified that `baseline-tiles-2026-07-28` was the only snapshot, Kasm was healthy, & `ssd-lvm2` read 53.87 percent before deletion.

```text
Command:
set -e
printf '%s\n' 'TIME'
date --iso-8601=seconds
printf '%s\n' 'VM_STATUS'
qm status 122
printf '%s\n' 'SNAPSHOTS'
qm listsnapshot 122
printf '%s\n' 'THIN_POOL'
lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent,lv_attr ssd-lvm2
printf '%s\n' 'KASM_HEALTH'
qm guest exec 122 -- curl -sk --max-time 10 https://127.0.0.1/api/__healthcheck

Standard output:
TIME
2026-07-29T23:56:35-04:00
VM_STATUS
status: running
SNAPSHOTS
`-> baseline-tiles-2026-07-28   2026-07-28 23:08:18     Kasm baseline 2026-07-28: 6 vCPU, 12 GiB, 200G disk, 34 tiles suffixed Normal/VPN/Malware/Target/Review/Full, three concurrent sessions
 `-> current                                            You are here!
THIN_POOL
  LV                                           LSize  Data%  Meta%  Attr
  snap_vm-122-disk-0_baseline-tiles-2026-07-28   0.00               Vri---tz-k
  snap_vm-122-disk-1_baseline-tiles-2026-07-28 200.00               Vri---tz-k
  ssd-lvm2                                     228.11 53.87  2.45   twi-aotz--
  vm-122-cloudinit                               0.00 9.38          Vwi-aotz--
  vm-122-disk-0                                  0.00 14.06         Vwi-aotz--
  vm-122-disk-1                                200.00 59.43         Vwi-aotz--
KASM_HEALTH
{
   "exitcode" : 0,
   "exited" : 1,
   "out-data" : "{\"ok\": true}"
}

Standard error: empty
Exit code: 0
```

No external VM backup existed. Deleting this snapshot removed the last local rollback point.

## Step 2: Delete the final snapshot and trim

I deleted `baseline-tiles-2026-07-28`, verified the empty snapshot tree, ran `fstrim -av`, & measured the pool before and after trim.

```text
Command:
set -e
qm delsnapshot 122 baseline-tiles-2026-07-28
printf '%s\n' 'SNAPSHOTS_AFTER_DELETE'
qm listsnapshot 122
printf '%s\n' 'THIN_POOL_AFTER_DELETE'
lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent,lv_attr ssd-lvm2
printf '%s\n' 'FSTRIM'
qm guest exec 122 -- fstrim -av
printf '%s\n' 'THIN_POOL_AFTER_TRIM'
lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent,lv_attr ssd-lvm2

Standard output:
  Logical volume "snap_vm-122-disk-1_baseline-tiles-2026-07-28" successfully removed.
  Logical volume "snap_vm-122-disk-0_baseline-tiles-2026-07-28" successfully removed.
SNAPSHOTS_AFTER_DELETE
`-> current                                             You are here!
THIN_POOL_AFTER_DELETE
  LV               LSize  Data%  Meta%  Attr
  ssd-lvm2         228.11 52.10  2.32   twi-aotz--
  vm-122-cloudinit   0.00 9.38          Vwi-aotz--
  vm-122-disk-0      0.00 14.06         Vwi-aotz--
  vm-122-disk-1    200.00 59.43         Vwi-aotz--
FSTRIM
{
   "exitcode" : 0,
   "exited" : 1,
   "out-data" : "/boot/efi: 98.2 MiB (102995968 bytes) trimmed on /dev/sda15\n/boot: 0 B (0 bytes) trimmed on /dev/sda16\n/: 865.4 MiB (907468800 bytes) trimmed on /dev/sda1\n"
}
THIN_POOL_AFTER_TRIM
  LV               LSize  Data%  Meta%  Attr
  ssd-lvm2         228.11 52.10  2.32   twi-aotz--
  vm-122-cloudinit   0.00 9.38          Vwi-aotz--
  vm-122-disk-0      0.00 14.06         Vwi-aotz--
  vm-122-disk-1    200.00 59.42         Vwi-aotz--

Standard error: empty
Exit code: 0
```

Removing the snapshot reduced pool data use by 1.77 percentage points, about 4.04 GiB. The trim submitted another 865.4 MiB from `/`; pool use remained 52.10 percent at two-decimal precision.

## Step 3: Verify zero snapshots and Kasm

I counted the remaining snapshots, read back discard, checked both storage layers, & verified every Kasm container.

```text
Command:
set -e
printf '%s\n' 'TIME'
date --iso-8601=seconds
printf '%s\n' 'SNAPSHOT_COUNT'
qm listsnapshot 122 | awk '/20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]/{count++} END{print count+0}'
printf '%s\n' 'SNAPSHOTS'
qm listsnapshot 122
printf '%s\n' 'VM_AND_DISK'
qm status 122
qm config 122 | grep '^scsi0:'
printf '%s\n' 'THIN_POOL'
lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent,lv_attr ssd-lvm2
printf '%s\n' 'FILESYSTEM'
qm guest exec 122 -- df -h /
printf '%s\n' 'KASM_HEALTH'
qm guest exec 122 -- curl -sk --max-time 10 https://127.0.0.1/api/__healthcheck
printf '%s\n' 'CONTAINERS'
qm guest exec 122 -- docker ps --format '{{.Names}}|{{.Status}}'

Standard output:
TIME
2026-07-29T23:57:01-04:00
SNAPSHOT_COUNT
0
SNAPSHOTS
`-> current                                             You are here!
VM_AND_DISK
status: running
scsi0: ssd-lvm2:vm-122-disk-1,discard=on,iothread=1,size=200G,ssd=1
THIN_POOL
  LV               LSize  Data%  Meta%  Attr
  ssd-lvm2         228.11 52.10  2.32   twi-aotz--
  vm-122-cloudinit   0.00 9.38          Vwi-aotz--
  vm-122-disk-0      0.00 14.06         Vwi-aotz--
  vm-122-disk-1    200.00 59.42         Vwi-aotz--
FILESYSTEM
{
   "exitcode" : 0,
   "exited" : 1,
   "out-data" : "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       193G  120G   74G  62% /\n"
}
KASM_HEALTH
{
   "exitcode" : 0,
   "exited" : 1,
   "out-data" : "{\"ok\": true}"
}
CONTAINERS
{
   "exitcode" : 0,
   "exited" : 1,
   "out-data" : "kasm_proxy|Up 31 minutes\nkasm_rdp_https_gateway|Up 31 minutes (healthy)\nkasm_rdp_gateway|Up 29 minutes (healthy)\nkasm_agent|Up 31 minutes (healthy)\nkasm_api|Up 31 minutes (healthy)\nkasm_manager|Up 31 minutes (healthy)\nkasm_guac|Up 31 minutes (healthy)\nkasm_db|Up 31 minutes (healthy)\n"
}

Standard error: empty
Exit code: 0
```

I verified the public NPM route from the Windows workstation.

```text
Working directory:
D:\Documents\Homelab

Command:
curl.exe -k -sS --max-time 20 -o NUL -w "ROOT HTTP %{http_code} in %{time_total}s`n" https://kasm.alphasecunited.com/; curl.exe -k -sS --max-time 20 -o NUL -w "HEALTH HTTP %{http_code} in %{time_total}s`n" https://kasm.alphasecunited.com/api/__healthcheck; Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

Standard output:
ROOT HTTP 200 in 0.053800s
HEALTH HTTP 200 in 0.027837s
2026-07-29 23:57:15 -04:00

Standard error: empty
Exit code: 0
```

VM 122 remained online throughout the deletion. It has zero snapshots, no external guest backup, & no rollback point until a new post-Parrot baseline is created.

## Follow-Up

I created `baseline-parrot-2026-07-30` at 2026-07-30 01:05:48 EDT after the controlled Parrot pull, tile readback, lane tests, and service checks passed. VM 122 then returned to exactly one snapshot.
