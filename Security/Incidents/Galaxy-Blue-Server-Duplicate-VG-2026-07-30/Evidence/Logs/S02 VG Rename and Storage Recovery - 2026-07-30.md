# S02 VG Rename and Storage Recovery

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Captured:** 2026-07-30 about 23:58 EDT  
**Target:** `blue-server`, 192.168.70.12  
**Mechanism:** SSH Manager `ssh_execute`, root shell  
**Working directory:** SSH Manager default

## Command

```sh
set -e
vgrename bJedeb-vXMR-NNKr-T3JG-LNCa-tgwK-yDjMGj pve-old-sata
pvscan --cache
printf '%s\n' '=== volume groups after rename ==='
vgs --units g -o vg_name,vg_uuid,vg_attr,vg_size,vg_free,pv_name,lv_count
printf '%s\n' '=== Proxmox storage after rename ==='
pvesm status
printf '%s\n' '=== local-lvm contents ==='
pvesm list local-lvm
```

## Standard output

```text
  Processing VG pve because of matching UUID bJedeb-vXMR-NNKr-T3JG-LNCa-tgwK-yDjMGj
  Volume group "bJedeb-vXMR-NNKr-T3JG-LNCa-tgwK-yDjMGj" successfully renamed to "pve-old-sata"
  pvscan[16263] PV /dev/sda3 online.
  pvscan[16263] PV /dev/nvme0n1p3 online.
=== volume groups after rename ===
  VG           VG UUID                                Attr   VSize   VFree  PV             #LV
  pve          bpWw0Q-DQfZ-7fIy-hVqF-z94V-OEzd-11RP2e wz--n- 237.47g 16.00g /dev/nvme0n1p3   6
  pve-old-sata bJedeb-vXMR-NNKr-T3JG-LNCa-tgwK-yDjMGj wz--n- 237.00g 16.00g /dev/sda3        3
=== Proxmox storage after rename ===
Name             Type     Status     Total (KiB)      Used (KiB) Available (KiB)        %
hddpool-1     zfspool   disabled               0               0               0      N/A
local             dir     active        71017632         5873336        61491076    8.27%
local-lvm     lvmthin     active       148086784        16393206       131693577   11.07%
ssd-lvm1      lvmthin   disabled               0               0               0      N/A
ssd-lvm2      lvmthin   disabled               0               0               0      N/A
=== local-lvm contents ===
Volid                   Format  Type             Size VMID
local-lvm:vm-104-disk-0 raw     rootdir   17179869184 104
local-lvm:vm-107-disk-0 raw     rootdir   34359738368 107
local-lvm:vm-108-disk-0 raw     rootdir   16106127360 108
```

## Standard error

```text
WARNING: VG name pve is used by VGs bpWw0Q-DQfZ-7fIy-hVqF-z94V-OEzd-11RP2e and bJedeb-vXMR-NNKr-T3JG-LNCa-tgwK-yDjMGj.
Fix duplicate VG names with vgrename uuid, a device filter, or system IDs.
```

The warning was emitted while `vgrename` still saw the pre-rename names. The post-command `vgs` and `pvesm` output shows the collision gone.

**Exit code:** `0`  
**Structured result:** `success: true`

