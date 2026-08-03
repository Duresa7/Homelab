# S04 Final Verification

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Captured:** 2026-07-31 00:04:46 EDT  
**Target:** `blue-server`, 192.168.70.12  
**Mechanism:** SSH Manager `ssh_execute`, root shell  
**Working directory:** SSH Manager default

## Command

```sh
date --iso-8601=seconds
printf '%s\n' '=== cluster ==='
pvecm status | sed -n '1,28p'
printf '%s\n' '=== storage ==='
pvesm status
printf '%s\n' '=== LVM and disks ==='
pvs --units g -o pv_name,pv_uuid,pv_size,pv_free,vg_name,vg_uuid
vgs --units g -o vg_name,vg_uuid,vg_size,vg_free,pv_name,lv_count
lsblk -o NAME,PATH,MODEL,SERIAL,SIZE,TYPE,PTTYPE,FSTYPE,MOUNTPOINTS /dev/nvme0n1 /dev/sda
printf '%s\n' '=== guests and HA ==='
pct list
ha-manager status
ha-manager rules list
printf '%s\n' '=== CT 104 monitoring ==='
pct exec 104 -- bash -lc 'curl -fsS http://127.0.0.1:9090/-/ready; curl -fsS http://127.0.0.1:3000/api/health; docker ps --format "{{.Names}}|{{.Status}}"'
printf '%s\n' '=== CT 107 workloads ==='
pct exec 107 -- docker ps --format '{{.Names}}|{{.Status}}'
printf '%s\n' '=== CT 108 workloads ==='
pct exec 108 -- docker ps --format '{{.Names}}|{{.Status}}'
printf '%s\n' '=== activation errors after repair ==='
journalctl -b --since '2026-07-30 23:58:50' --no-pager -g 'activating LV|VG name pve|Multiple VGs' || true
```

## Standard output

```text
2026-07-31T00:04:46-04:00
=== cluster ===
Cluster information
-------------------
Name:             Galaxy
Config Version:   8
Transport:        knet
Secure auth:      on

Quorum information
------------------
Date:             Fri Jul 31 00:04:47 2026
Quorum provider:  corosync_votequorum
Nodes:            4
Node ID:          0x00000003
Ring ID:          1.236
Quorate:          Yes

Votequorum information
----------------------
Expected votes:   4
Highest expected: 4
Total votes:      4
Quorum:           3
Flags:            Quorate

Membership information
----------------------
    Nodeid      Votes Name
0x00000001          1 192.168.70.10
=== storage ===
Name             Type     Status     Total (KiB)      Used (KiB) Available (KiB)        %
hddpool-1     zfspool   disabled               0               0               0      N/A
local             dir     active        71017632         5873632        61490780    8.27%
local-lvm     lvmthin     active       148086784        16393206       131693577   11.07%
ssd-lvm1      lvmthin   disabled               0               0               0      N/A
ssd-lvm2      lvmthin   disabled               0               0               0      N/A
=== LVM and disks ===
  PV             PV UUID                                PSize   PFree  VG  VG UUID
  /dev/nvme0n1p3 Ka1ZeG-jzer-nW50-Hxzp-CcFD-WFGR-NjIkXG 237.47g 16.00g pve bpWw0Q-DQfZ-7fIy-hVqF-z94V-OEzd-11RP2e
  VG  VG UUID                                VSize   VFree  PV             #LV
  pve bpWw0Q-DQfZ-7fIy-hVqF-z94V-OEzd-11RP2e 237.47g 16.00g /dev/nvme0n1p3   6
NAME                         PATH                             MODEL                      SERIAL                    SIZE TYPE PTTYPE FSTYPE      MOUNTPOINTS
sda                          /dev/sda                         WDC WD5000LPVX-08V0TT5     [redacted; suffix 6NSN] 465.8G disk
nvme0n1                      /dev/nvme0n1                     SAMSUNG MZVLW256HEHP-000L7 [redacted; suffix 1210] 238.5G disk gpt
├─nvme0n1p1                  /dev/nvme0n1p1                                                               1007K part gpt
├─nvme0n1p2                  /dev/nvme0n1p2                                                                  1G part gpt    vfat        /boot/efi
└─nvme0n1p3                  /dev/nvme0n1p3                                                              237.5G part gpt    LVM2_member
  ├─pve-swap                 /dev/mapper/pve-swap                                                            8G lvm         swap        [SWAP]
  ├─pve-root                 /dev/mapper/pve-root                                                         69.4G lvm         ext4        /
  ├─pve-data_tmeta           /dev/mapper/pve-data_tmeta                                                    1.4G lvm
  │ └─pve-data-tpool         /dev/mapper/pve-data-tpool                                                  141.2G lvm
  │   ├─pve-data             /dev/mapper/pve-data                                                        141.2G lvm
  │   ├─pve-vm--104--disk--0 /dev/mapper/pve-vm--104--disk--0                                               16G lvm         ext4
  │   ├─pve-vm--107--disk--0 /dev/mapper/pve-vm--107--disk--0                                               32G lvm         ext4
  │   └─pve-vm--108--disk--0 /dev/mapper/pve-vm--108--disk--0                                               15G lvm         ext4
  └─pve-data_tdata           /dev/mapper/pve-data_tdata                                                  141.2G lvm
    └─pve-data-tpool         /dev/mapper/pve-data-tpool                                                  141.2G lvm
      ├─pve-data             /dev/mapper/pve-data                                                        141.2G lvm
      ├─pve-vm--104--disk--0 /dev/mapper/pve-vm--104--disk--0                                               16G lvm         ext4
      ├─pve-vm--107--disk--0 /dev/mapper/pve-vm--107--disk--0                                               32G lvm         ext4
      └─pve-vm--108--disk--0 /dev/mapper/pve-vm--108--disk--0                                               15G lvm         ext4
=== guests and HA ===
VMID       Status     Lock         Name
104        running                 monitor-01
107        running                 docker-network
108        running                 docker-blue
quorum OK
master red-server (active, Fri Jul 31 00:04:49 2026)
fencing armed (CRM watchdog active)
lrm blue-server (active, watchdog active, Fri Jul 31 00:04:47 2026)
lrm grey-server (idle, watchdog standby, Fri Jul 31 00:04:49 2026)
lrm purple-server (idle, watchdog standby, Fri Jul 31 00:04:49 2026)
lrm red-server (idle, watchdog standby, Fri Jul 31 00:04:49 2026)
service ct:107 (blue-server, started)
service ct:108 (blue-server, started)
┌────────────────────────┐
│ rule                   │
╞════════════════════════╡
│ pin-blue-local-storage │
└────────────────────────┘
=== CT 104 monitoring ===
Prometheus Server is Ready.
{
  "database": "ok",
  "version": "13.1.1",
  "commit": "a9cee6e1724a455676bb6c05eef7fc54aa4b19f4"
}grafana|Up 5 minutes
peanut|Up 5 minutes (healthy)
blackbox-exporter|Up 5 minutes
pve-exporter|Up 5 minutes
prometheus|Up 2 minutes
nut-exporter|Up 5 minutes
cadvisor|Up 5 minutes (healthy)
=== CT 107 workloads ===
netbird-server|Up 5 minutes
netbird-dashboard|Up 5 minutes
portainer_edge_agent|Up 5 minutes
cadvisor|Up 5 minutes (healthy)
nginx-proxy-manager|Up 5 minutes (healthy)
=== CT 108 workloads ===
hbbs|Up 5 minutes
hbbr|Up 5 minutes
portainer_edge_agent|Up 5 minutes
cadvisor|Up 5 minutes (healthy)
=== activation errors after repair ===
-- No entries --
```

## Standard error

Empty.

**Exit code:** `0`  
**Structured result:** `success: true`

