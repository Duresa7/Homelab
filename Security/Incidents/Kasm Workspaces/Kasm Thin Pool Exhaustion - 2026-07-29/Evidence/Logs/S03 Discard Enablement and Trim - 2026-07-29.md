# S03 Discard Enablement and Trim

**Created:** 2026-07-29  
**Last updated:** 2026-07-29

**Incident:** [Kasm Workspaces Thin Pool Exhaustion](../../Kasm-Workspaces-Incident-Report-2026-07-29-Thin-Pool-Exhaustion.md)

## Capture

- Capture completed: 2026-07-29 23:28 EDT
- Proxmox target: `purple-server`
- Guest target: `kasm-01`, VM 122
- Remote mechanism: SSH Manager MCP to a Bash shell on `purple-server`
- Guest mechanism: Proxmox QEMU guest agent
- Local verification mechanism: Windows PowerShell with `curl.exe`

## Step 1: Verify the starting state

I checked the running state, disk configuration, snapshots, thin-pool allocation, & guest agent before changing VM 122.

```text
Command:
set -e
printf '%s\n' 'VM_STATUS'
qm status 122
printf '%s\n' 'DISK_CONFIG'
qm config 122 | grep '^scsi0:'
printf '%s\n' 'SNAPSHOTS'
qm listsnapshot 122
printf '%s\n' 'THIN_POOL'
lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent,lv_attr ssd-lvm2
printf '%s\n' 'GUEST_AGENT'
qm agent 122 ping

Standard output:
VM_STATUS
status: running
DISK_CONFIG
scsi0: ssd-lvm2:vm-122-disk-1,iothread=1,size=200G,ssd=1
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
  ssd-lvm2                                             228.11 54.91  2.59   twi-aotz--
  vm-122-cloudinit                                       0.00 9.38          Vwi-aotz--
  vm-122-disk-0                                          0.00 14.06         Vwi-aotz--
  vm-122-disk-1                                        200.00 60.03         Vwi-aotz--
GUEST_AGENT

Standard error: empty
Exit code: 0
```

VM 122 was running with two snapshots. The 200 GiB `scsi0` lacked a discard option, and `ssd-lvm2` read 54.91 percent.

## Step 2: Enable discard

I shut down VM 122 through ACPI and verified that Proxmox reported it stopped.

```text
Command:
qm shutdown 122 --timeout 180 && qm status 122

Standard output:
status: stopped

Standard error: empty
Exit code: 0
```

I updated the existing disk entry in place. I didn't replace its volume or touch either snapshot.

```text
Command:
set -e
qm set 122 --scsi0 ssd-lvm2:vm-122-disk-1,discard=on,iothread=1,size=200G,ssd=1
qm config 122 | grep '^scsi0:'

Standard output:
update VM 122: -scsi0 ssd-lvm2:vm-122-disk-1,discard=on,iothread=1,size=200G,ssd=1
scsi0: ssd-lvm2:vm-122-disk-1,discard=on,iothread=1,size=200G,ssd=1

Standard error: empty
Exit code: 0
```

## Step 3: Start the VM

I started VM 122, read back the disk option, & waited for the guest agent.

```text
Command:
set -e
qm start 122
qm status 122
qm config 122 | grep '^scsi0:'

Standard output:
generating cloud-init ISO
status: running
scsi0: ssd-lvm2:vm-122-disk-1,discard=on,iothread=1,size=200G,ssd=1

Standard error: empty
Exit code: 0
```

```text
Command:
for i in $(seq 1 12); do if qm agent 122 ping >/dev/null 2>&1; then echo 'guest-agent: ready'; exit 0; fi; sleep 5; done; echo 'guest-agent: not ready after 60 seconds'; exit 1

Standard output:
guest-agent: ready

Standard error: empty
Exit code: 0
```

## Step 4: Trim unused guest blocks

I measured the thin pool, ran `fstrim -av` through the guest agent, & measured the pool again.

```text
Command:
set -e
printf '%s\n' 'THIN_POOL_BEFORE'
lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent --select 'lv_name=ssd-lvm2'
printf '%s\n' 'FSTRIM'
qm guest exec 122 -- fstrim -av
printf '%s\n' 'THIN_POOL_AFTER'
lvs --units g --nosuffix -o lv_name,lv_size,data_percent,metadata_percent --select 'lv_name=ssd-lvm2'

Standard output:
THIN_POOL_BEFORE
  LV       LSize  Data%  Meta%
  ssd-lvm2 228.11 54.91  2.60
FSTRIM
{
   "exitcode" : 0,
   "exited" : 1,
   "out-data" : "/boot/efi: 98.2 MiB (102995968 bytes) trimmed on /dev/sda15\n/boot: 757.9 MiB (794685440 bytes) trimmed on /dev/sda16\n/: 72.7 GiB (78028627968 bytes) trimmed on /dev/sda1\n"
}
THIN_POOL_AFTER
  LV       LSize  Data%  Meta%
  ssd-lvm2 228.11 54.78  2.60

Standard error: empty
Exit code: 0
```

The guest submitted 72.7 GiB of discard requests for `/`, but the thin pool released about 0.13 percentage points. Both retained snapshots still reference most of the old blocks.

## Step 5: Verify Kasm and the public route

Docker completed its normal startup sequence. The final readback showed all eight containers running, with seven health checks passing and `kasm_proxy` carrying no health check by design.

```text
Command:
qm guest exec 122 -- docker ps --format '{{.Names}}|{{.Status}}'

Standard output:
{
   "exitcode" : 0,
   "exited" : 1,
   "out-data" : "kasm_proxy|Up 2 minutes\nkasm_rdp_https_gateway|Up 2 minutes (healthy)\nkasm_rdp_gateway|Up 39 seconds (healthy)\nkasm_agent|Up 2 minutes (healthy)\nkasm_api|Up 2 minutes (healthy)\nkasm_manager|Up 2 minutes (healthy)\nkasm_guac|Up 2 minutes (healthy)\nkasm_db|Up 2 minutes (healthy)\n"
}

Standard error: empty
Exit code: 0
```

The local API returned `{"ok": true}` during the startup verification. I then tested the public NPM route from the Windows workstation because the public hostname timed out from `purple-server`'s internal route.

```text
Working directory:
D:\Documents\Homelab

Command:
curl.exe -k -sS --max-time 20 -o NUL -w "ROOT HTTP %{http_code} in %{time_total}s`n" https://kasm.<YOUR_BASE_DOMAIN>/; curl.exe -k -sS --max-time 20 -o NUL -w "HEALTH HTTP %{http_code} in %{time_total}s`n" https://kasm.<YOUR_BASE_DOMAIN>/api/__healthcheck

Standard output:
ROOT HTTP 200 in 0.021883s
HEALTH HTTP 200 in 0.029965s

Standard error: empty
Exit code: 0
```

The final thin-pool readback was 54.80 percent data and 2.60 percent metadata. The brief rise from 54.78 percent occurred while Kasm finished starting and writing its runtime state.
