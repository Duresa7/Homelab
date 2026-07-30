# S04 Older Snapshot Removal

**Created:** 2026-07-29  
**Last updated:** 2026-07-29

**Incident:** [Kasm Workspaces Thin Pool Exhaustion](../../Kasm-Workspaces-Incident-Report-2026-07-29-Thin-Pool-Exhaustion.md)

## Capture

- Capture time: 2026-07-29 23:42 through 23:43 EDT
- Proxmox target: `purple-server`
- Guest target: `kasm-01`, VM 122
- Remote mechanism: SSH Manager MCP to a Bash shell on `purple-server`
- Local verification mechanism: Windows PowerShell with `curl.exe`

## Step 1: Verify the deletion target

I checked VM 122, both snapshots, `ssd-lvm2`, & the Kasm API before deleting anything.

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
2026-07-29T23:42:13-04:00
VM_STATUS
status: running
SNAPSHOTS
`-> pre-workspace-buildout-2026-07-28 2026-07-28 19:35:27     no-description
 `-> baseline-tiles-2026-07-28  2026-07-28 23:08:18     Kasm baseline 2026-07-28: 6 vCPU, 12 GiB, 200G disk, 34 tiles suffixed Normal/VPN/Malware/Target/Review/Full, three concurrent sessions
  `-> current                                           You are here!
THIN_POOL
  LV                                                   LSize  Data%  Meta%  Attr
  snap_vm-122-disk-0_baseline-tiles-2026-07-28           0.00               Vri---tz-k
  snap_vm-122-disk-0_pre-workspace-buildout-2026-07-28   0.00               Vri---tz-k
  snap_vm-122-disk-1_baseline-tiles-2026-07-28         200.00               Vri---tz-k
  snap_vm-122-disk-1_pre-workspace-buildout-2026-07-28 150.00               Vri---tz-k
  ssd-lvm2                                             228.11 54.79  2.60   twi-aotz--
  vm-122-cloudinit                                       0.00 9.38          Vwi-aotz--
  vm-122-disk-0                                          0.00 14.06         Vwi-aotz--
  vm-122-disk-1                                        200.00 59.87         Vwi-aotz--
KASM_HEALTH
{
   "exitcode" : 0,
   "exited" : 1,
   "out-data" : "{\"ok\": true}"
}

Standard error: empty
Exit code: 0
```

The deletion target was `pre-workspace-buildout-2026-07-28`, created at 19:35:27 EDT. The retained recovery point was the separate `baseline-tiles-2026-07-28` snapshot created at 23:08:18 EDT.

## Step 2: Delete the older snapshot

I deleted only the pre-build snapshot and read the remaining snapshot tree plus every thin volume afterward.

```text
Command:
set -e
qm delsnapshot 122 pre-workspace-buildout-2026-07-28
printf '%s\n' 'SNAPSHOTS_AFTER'
qm listsnapshot 122
printf '%s\n' 'THIN_POOL_AFTER'
lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent,lv_attr ssd-lvm2

Standard output:
  Logical volume "snap_vm-122-disk-1_pre-workspace-buildout-2026-07-28" successfully removed.
  Logical volume "snap_vm-122-disk-0_pre-workspace-buildout-2026-07-28" successfully removed.
SNAPSHOTS_AFTER
`-> baseline-tiles-2026-07-28   2026-07-28 23:08:18     Kasm baseline 2026-07-28: 6 vCPU, 12 GiB, 200G disk, 34 tiles suffixed Normal/VPN/Malware/Target/Review/Full, three concurrent sessions
 `-> current                                            You are here!
THIN_POOL_AFTER
  LV                                           LSize  Data%  Meta%  Attr
  snap_vm-122-disk-0_baseline-tiles-2026-07-28   0.00               Vri---tz-k
  snap_vm-122-disk-1_baseline-tiles-2026-07-28 200.00               Vri---tz-k
  ssd-lvm2                                     228.11 53.85  2.44   twi-aotz--
  vm-122-cloudinit                               0.00 9.38          Vwi-aotz--
  vm-122-disk-0                                  0.00 14.06         Vwi-aotz--
  vm-122-disk-1                                200.00 59.87         Vwi-aotz--

Standard error: empty
Exit code: 0
```

The deletion removed both thin volumes associated with the older Proxmox snapshot. Pool data use fell from 54.79 to 53.85 percent, which returned about 2.14 GiB from the 228.11 GiB pool.

## Step 3: Verify one snapshot and Kasm

I counted the dated snapshots, read the live disk option, checked the pool, & checked every Kasm container.

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
printf '%s\n' 'KASM_HEALTH'
qm guest exec 122 -- curl -sk --max-time 10 https://127.0.0.1/api/__healthcheck
printf '%s\n' 'CONTAINERS'
qm guest exec 122 -- docker ps --format '{{.Names}}|{{.Status}}'

Standard output:
TIME
2026-07-29T23:42:52-04:00
SNAPSHOT_COUNT
1
SNAPSHOTS
`-> baseline-tiles-2026-07-28   2026-07-28 23:08:18     Kasm baseline 2026-07-28: 6 vCPU, 12 GiB, 200G disk, 34 tiles suffixed Normal/VPN/Malware/Target/Review/Full, three concurrent sessions
 `-> current                                            You are here!
VM_AND_DISK
status: running
scsi0: ssd-lvm2:vm-122-disk-1,discard=on,iothread=1,size=200G,ssd=1
THIN_POOL
  LV                                           LSize  Data%  Meta%  Attr
  snap_vm-122-disk-0_baseline-tiles-2026-07-28   0.00               Vri---tz-k
  snap_vm-122-disk-1_baseline-tiles-2026-07-28 200.00               Vri---tz-k
  ssd-lvm2                                     228.11 53.85  2.44   twi-aotz--
  vm-122-cloudinit                               0.00 9.38          Vwi-aotz--
  vm-122-disk-0                                  0.00 14.06         Vwi-aotz--
  vm-122-disk-1                                200.00 59.87         Vwi-aotz--
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
   "out-data" : "kasm_proxy|Up 17 minutes\nkasm_rdp_https_gateway|Up 17 minutes (healthy)\nkasm_rdp_gateway|Up 15 minutes (healthy)\nkasm_agent|Up 17 minutes (healthy)\nkasm_api|Up 17 minutes (healthy)\nkasm_manager|Up 17 minutes (healthy)\nkasm_guac|Up 17 minutes (healthy)\nkasm_db|Up 17 minutes (healthy)\n"
}

Standard error: empty
Exit code: 0
```

I verified the public NPM route from the Windows workstation.

```text
Working directory:
D:\Documents\Homelab

Command:
curl.exe -k -sS --max-time 20 -o NUL -w "ROOT HTTP %{http_code} in %{time_total}s`n" https://kasm.<YOUR_BASE_DOMAIN>/; curl.exe -k -sS --max-time 20 -o NUL -w "HEALTH HTTP %{http_code} in %{time_total}s`n" https://kasm.<YOUR_BASE_DOMAIN>/api/__healthcheck; Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

Standard output:
ROOT HTTP 200 in 0.031308s
HEALTH HTTP 200 in 0.030693s
2026-07-29 23:43:04 -04:00

Standard error: empty
Exit code: 0
```

VM 122 remained online throughout the snapshot deletion. One snapshot exists, `discard=on` remains set, all eight containers run, all seven defined health checks pass, & both public endpoints return HTTP `200`.
