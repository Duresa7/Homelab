# Galaxy Nodes Post-Blue SATA Wipe Snapshot

**Created:** 2026-07-31  
**Last updated:** 2026-07-31  
**Snapshot date:** 2026-07-31

I carried the complete node and physical-storage inventory forward after adding a 500 GB WDC HDD to `blue-server`. The disk retained an older Proxmox layout whose `pve` VG name collided with Blue's current NVMe VG. I wiped the WDC layout after verifying Blue's mounted root and all three LXC disks remained on the NVMe.

Galaxy has four nodes with 24 physical CPU cores, 105.21 GiB of memory, four NVMe boot devices, two SATA SSDs, one 1.82 TiB ZFS disk, one 931.51 GiB media HDD, & one blank 465.8 GiB HDD in Blue.

## Nodes

| Node | IP | CPU | Cores / Threads | Memory | GPU | Physical storage | Power source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| blue-server | 192.168.70.12 | Intel Core i5-7500T @ 2.70GHz | 4 / 4 | 11.57 GiB | Intel HD Graphics 630, integrated | 1x NVMe, 1x HDD | [UPS-02](../../../Infrastructure/Hardware/Power.md) |
| grey-server | 192.168.70.10 | AMD Ryzen 7 3700X | 8 / 16 | 62.72 GiB | NVIDIA GeForce GTX 1080 Ti, discrete | 1x NVMe, 1x SSD, 1x HDD | [UPS-02](../../../Infrastructure/Hardware/Power.md) |
| purple-server | 192.168.70.11 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x SSD | Not reported |
| red-server | 192.168.70.13 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x HDD | [UPS-01; also reported on UPS-02](../../../Infrastructure/Hardware/Power.md) |

## Physical storage

| Node | Device | Type | Model | Size | Used by |
| --- | --- | --- | --- | --- | --- |
| blue-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLW256HEHP-000L7 | 238.47 GiB | BIOS boot, root, swap, `local-lvm`, CTs 104/107/108 |
| blue-server | /dev/sda | HDD | WDC WD5000LPVX-08V0TT5 | 465.76 GiB | Blank and unallocated; stale Proxmox layout wiped 2026-07-31 |
| grey-server | /dev/nvme0n1 | NVMe | CT1000P310SSD8 | 931.51 GiB | BIOS boot |
| grey-server | /dev/sda | SSD | CT2000BX500SSD1 | 1.82 TiB | LVM |
| grey-server | /dev/sdb | HDD | TOSHIBA_DT01ACA200 | 1.82 TiB | ZFS |
| purple-server | /dev/nvme0n1 | NVMe | THNSF5256GPUK TOSHIBA | 238.47 GiB | BIOS boot |
| purple-server | /dev/sda | SSD | Samsung SSD 850 EVO 250GB | 232.89 GiB | `ssd-lvm2` LVM-thin; VM and LXC images; VM 122 |
| red-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLB256HAHQ-000L7 | 238.47 GiB | BIOS boot |
| red-server | /dev/sda | HDD | ST1000LM035-1RK172 | 931.51 GiB | CT 842 `/data` through host ext4 bind mount |

The final LVM readback reported one PV, `/dev/nvme0n1p3`, in VG `pve`. `local-lvm` was active at 11.07 percent used. `/dev/sda` had no partition table, filesystem, UUID, mount, or `wipefs` signature.

The WDC SMART capture reported `PASSED`, 23,204 power-on hours, and zero reallocated, pending, offline-uncorrectable, or CRC-error sectors. The [drive inventory](../../../Infrastructure/Hardware/Components/Drives/README.md) links the raw output. The [duplicate VG record](../../../Infrastructure/Compute/Galaxy/Documentation/Troubleshooting/Duplicate%20pve%20Volume%20Group%20on%20blue-server%20-%202026-07-30.md) records the outage and repair.

## Memory modules

![Two SK hynix SO-DIMM memory modules](../../../Infrastructure/Hardware/Images/image-1776104321961.jpg)

The retained photo shows two SK hynix SO-DIMM modules from the node hardware.

