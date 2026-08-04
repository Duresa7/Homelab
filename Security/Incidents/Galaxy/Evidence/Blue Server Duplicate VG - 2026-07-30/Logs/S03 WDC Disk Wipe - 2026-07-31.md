# S03 WDC Disk Wipe

**Created:** 2026-07-31  
**Last updated:** 2026-07-31

**Captured:** 2026-07-31 about 00:00 EDT  
**Target:** `blue-server`, 192.168.70.12  
**Mechanism:** SSH Manager `ssh_execute`, root shell  
**Working directory:** SSH Manager default

## Guarded destructive command

```sh
set -eu
blue_disk=/dev/sda
blue_expected_serial=<REDACTED_BLUE_HDD_SERIAL>
blue_expected_vg_uuid=bJedeb-vXMR-NNKr-T3JG-LNCa-tgwK-yDjMGj
blue_serial=$(lsblk -dn -o SERIAL "$blue_disk" | xargs)
blue_model=$(lsblk -dn -o MODEL "$blue_disk" | xargs)
blue_size=$(lsblk -dn -o SIZE "$blue_disk" | xargs)
blue_mounts=$(lsblk -nr -o MOUNTPOINTS "$blue_disk" | sed '/^[[:space:]]*$/d' || true)
blue_stale_uuid=$(vgs --noheadings -o vg_uuid pve-old-sata | xargs)
blue_active_pv=$(pvs --noheadings --select 'vg_name=pve' -o pv_name | xargs)
blue_root_source=$(findmnt -no SOURCE /)
printf 'Validated target: %s | %s | %s | serial %s\n' "$blue_disk" "$blue_model" "$blue_size" "$blue_serial"
test "$blue_serial" = "$blue_expected_serial"
test -z "$blue_mounts"
test "$blue_stale_uuid" = "$blue_expected_vg_uuid"
test "$blue_active_pv" = /dev/nvme0n1p3
test "$blue_root_source" = /dev/mapper/pve-root
vgremove -y pve-old-sata
pvremove -y /dev/sda3
wipefs --all --force /dev/sda1 /dev/sda2 /dev/sda3
sgdisk --zap-all "$blue_disk"
wipefs --all --force "$blue_disk"
partprobe "$blue_disk"
udevadm settle
```

## Standard output

```text
Validated target: /dev/sda | WDC WD5000LPVX-08V0TT5 | 465.8G | serial <REDACTED_BLUE_HDD_SERIAL>
  Logical volume "data" successfully removed.
  Logical volume "swap" successfully removed.
  Logical volume "root" successfully removed.
  Volume group "pve-old-sata" successfully removed
  Labels on physical volume "/dev/sda3" successfully wiped.
/dev/sda2: 8 bytes were erased at offset 0x00000052 (vfat): 46 41 54 33 32 20 20 20
/dev/sda2: 1 byte was erased at offset 0x00000000 (vfat): eb
/dev/sda2: 2 bytes were erased at offset 0x000001fe (vfat): 55 aa
GPT data structures destroyed! You may now partition the disk using fdisk or
other utilities.
```

## Standard error and partial result

```text
sh: 23: partprobe: not found
```

**Exit code:** `127`  
**Structured result:** `success: false`

The destructive operations completed before the missing refresh utility stopped the shell. I did not repeat them.

## Follow-up verification command

```sh
set -e
blockdev --rereadpt /dev/sda
udevadm settle
printf '%s\n' '=== blank WDC disk ==='
lsblk -o NAME,PATH,MODEL,SERIAL,SIZE,TYPE,PTTYPE,FSTYPE,UUID,MOUNTPOINTS /dev/sda
printf '%s\n' '=== residual signatures ==='
wipefs --no-act /dev/sda
printf '%s\n' '=== remaining LVM state ==='
pvs --units g -o pv_name,pv_uuid,pv_size,pv_free,vg_name,vg_uuid
vgs --units g -o vg_name,vg_uuid,vg_size,vg_free,pv_name,lv_count
```

## Follow-up output

```text
=== blank WDC disk ===
NAME PATH     MODEL                  SERIAL                          SIZE TYPE PTTYPE FSTYPE UUID MOUNTPOINTS
sda  /dev/sda WDC WD5000LPVX-08V0TT5 [redacted; suffix 6NSN]       465.8G disk
=== residual signatures ===
=== remaining LVM state ===
  PV             PV UUID                                PSize   PFree  VG  VG UUID
  /dev/nvme0n1p3 Ka1ZeG-jzer-nW50-Hxzp-CcFD-WFGR-NjIkXG 237.47g 16.00g pve bpWw0Q-DQfZ-7fIy-hVqF-z94V-OEzd-11RP2e
  VG  VG UUID                                VSize   VFree  PV             #LV
  pve bpWw0Q-DQfZ-7fIy-hVqF-z94V-OEzd-11RP2e 237.47g 16.00g /dev/nvme0n1p3   6
```

**Exit code:** `0`  
**Structured result:** `success: true`
