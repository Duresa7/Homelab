# S00 Compute and Storage Final Verification

**Created:** 2026-07-28  
**Last updated:** 2026-07-31

**Capture timestamp:** 2026-07-28T14:40:41-04:00  
**Target:** `purple-server`  
**Mechanism:** SSH Manager MCP, remote Bash, default working directory

## Exact command

```bash
date -Is; pvecm status | grep -E '^(Nodes:|Quorate:|Expected votes:|Total votes:)'; qm status 122; qm config 122 | grep -E '^(agent|cores|efidisk0|ide2|ipconfig0|memory|name|nameserver|net[0-3]|onboot|scsi0):'; pvesm status --storage ssd-lvm2; qm listsnapshot 122; smartctl -H /dev/sda; smartctl -A /dev/sda | grep -Ei 'Reallocated_Sector_Ct|Power_On_Hours|Wear_Leveling_Count|Uncorrectable_Error_Cnt|CRC_Error_Count'
```

## Complete standard output

```text
2026-07-28T14:40:41-04:00
Nodes:            4
Quorate:          Yes
Expected votes:   4
Total votes:      4
status: running
agent: enabled=1
cores: 4
efidisk0: ssd-lvm2:vm-122-disk-0,efitype=4m,pre-enrolled-keys=0,size=528K
ide2: ssd-lvm2:vm-122-cloudinit,media=cdrom,size=4M
ipconfig0: ip=192.168.78.10/24,gw=192.168.78.1
memory: 8192
name: kasm-01
nameserver: 9.9.9.9
net0: virtio=<YOUR_KASM_HOST_MAC>,bridge=vmbr0,firewall=1,tag=78
net1: virtio=<YOUR_KASM_LANE_74_MAC>,bridge=vmbr0,firewall=0,tag=74
net2: virtio=<YOUR_KASM_LANE_77_MAC>,bridge=vmbr0,firewall=0,tag=77
net3: virtio=<YOUR_KASM_LANE_79_MAC>,bridge=vmbr0,firewall=0,tag=79
onboot: 1
scsi0: ssd-lvm2:vm-122-disk-1,iothread=1,size=100G,ssd=1
Name            Type     Status     Total (KiB)      Used (KiB) Available (KiB)        %
ssd-lvm2     lvmthin     active       239185920        26501799       212684120   11.08%
`-> current                                             You are here!
smartctl 7.5 2025-04-30 r5714 [x86_64-linux-7.0.14-6-pve] (local build)
Copyright (C) 2002-25, Bruce Allen, Christian Franke, www.smartmontools.org

=== START OF READ SMART DATA SECTION ===
SMART overall-health self-assessment test result: PASSED

  5 Reallocated_Sector_Ct   0x0033   100   100   010    Pre-fail  Always       -       0
  9 Power_On_Hours          0x0032   091   091   000    Old_age   Always       -       45242
177 Wear_Leveling_Count     0x0013   015   015   000    Pre-fail  Always       -       1801
187 Uncorrectable_Error_Cnt 0x0032   100   100   000    Old_age   Always       -       0
199 CRC_Error_Count         0x003e   100   100   000    Old_age   Always       -       0
```

**Standard error:** empty  
**Exit code:** 0  
**Structured result:** `success: true`

The follow-up query itself verifies four-node quorum, VM state and placement, pool state, the absence of a named snapshot, and the final SMART counters. The unchanged full SMART output is stored with the [drive inventory](../../../../../Infrastructure/Hardware/Components/Drives/SSD/smartctl-a_Samsung-850EVO-250GB_252T_2026-07-28.txt).
