# Galaxy Node Spec Sheet

**Created:** 2026-07-08  
**Last updated:** 2026-07-31

I run Galaxy as five nodes with 30 physical CPU cores, 114.78 GiB of usable memory, five NVMe boot devices, two SATA SSDs, and four SATA HDDs. Blue's 465.76 GiB HDD is unused while its extended test runs. Green's 298.09 GiB HDD is blank but failed its extended test and must not receive data. I keep each model, capacity, management address, and reported UPS assignment separate.

## Nodes
| Node | IP | CPU | Cores / Threads | Memory | GPU | Physical storage | Power source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| blue-server | 192.168.70.12 | Intel Core i5-7500T @ 2.70GHz | 4 / 4 | 5.68 GiB | Intel HD Graphics 630, integrated | 1x NVMe, 1x HDD | [UPS-02](Power.md) |
| green-server | 192.168.70.14 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x HDD | Not reported |
| grey-server | 192.168.70.10 | AMD Ryzen 7 3700X | 8 / 16 | 62.72 GiB | NVIDIA GeForce GTX 1080 Ti, discrete | 1x NVMe, 1x SSD, 1x HDD | [UPS-02](Power.md) |
| purple-server | 192.168.70.11 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x SSD | Not reported |
| red-server | 192.168.70.13 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x HDD | [UPS-01; also reported on UPS-02](Power.md) |

## Physical Storage
| Node | Device | Type | Model | Size | Used by |
| --- | --- | --- | --- | --- | --- |
| blue-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLW256HEHP-000L7 | 238.47 GiB | Proxmox boot, root, swap, and `local-lvm` |
| blue-server | /dev/sda | HDD | WDC WD5000LPVX-08V0TT5 | 465.76 GiB | Unused; empty GPT, no filesystem or LVM; passed its extended SMART test |
| green-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLB256HAHQ-000L7 | 238.47 GiB | Proxmox boot, root, swap, and `local-lvm` |
| green-server | /dev/sda | HDD | HITACHI HTS723232A7A364 | 298.09 GiB | Blank; extended test stopped with a read failure and two pending sectors; do not use |
| grey-server | /dev/nvme0n1 | NVMe | CT1000P310SSD8 | 931.51 GiB | BIOS boot |
| grey-server | /dev/sda | SSD | CT2000BX500SSD1 | 1.82 TiB | LVM |
| grey-server | /dev/sdb | HDD | TOSHIBA_DT01ACA200 | 1.82 TiB | ZFS |
| purple-server | /dev/nvme0n1 | NVMe | THNSF5256GPUK TOSHIBA | 238.47 GiB | BIOS boot |
| purple-server | /dev/sda | SSD | Samsung SSD 850 EVO 250GB | 232.89 GiB | `ssd-lvm2` LVM-thin; VM and LXC images; VM 122 |
| red-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLB256HAHQ-000L7 | 238.47 GiB | BIOS boot |
| red-server | /dev/sda | HDD | ST1000LM035-1RK172 | 931.51 GiB | CT 842 `/data` through host ext4 bind mount |

Purple's boot device changed on 2026-07-25. The Samsung MZVLB256HAHQ-000L7 that shipped in it wore out at 169% of rated endurance, so I cloned it onto the Toshiba THNSF5256GPUK listed above & added the 850 EVO on the SATA port at the same time. On 2026-07-28 I configured the 850 EVO as `ssd-lvm2`, restricted the pool to Purple, and moved Kasm VM 122 onto it. Both drives and the retired Samsung are in the [drive inventory](Components/Drives/README.md); the swap is written up in [Purple Boot NVMe Replacement](../Compute/Galaxy/Documentation/Change%20Records/Purple%20Boot%20NVMe%20Replacement%20-%202026-07-25.md).

I added Blue's WDC HDD before the 2026-07-30 shutdown. It retained an older Proxmox VG named `pve`, which collided with Blue's live NVMe VG at the next boot. I verified the NVMe held the mounted root and all three guest volumes, then wiped the WDC partition table and signatures after confirming its old layout wasn't needed. The [duplicate VG troubleshooting record](../Compute/Galaxy/Documentation/Troubleshooting/Duplicate%20pve%20Volume%20Group%20on%20blue-server%20-%202026-07-30.md) records the repair.

That WDC disk then passed a full extended SMART read on 2026-07-31 at 23,215 power-on hours with zero reallocated, pending, offline-uncorrectable, & CRC-error sectors. It now carries an empty GPT written by a Proxmox `diskinit` task at 09:10 EDT the same day, so `wipefs` reports a `gpt` label where the 00:00 wipe had left none. It holds no partition, filesystem, or LVM PV.

I added Green's Hitachi HDD during the five-node expansion. Its extended SMART test stopped at 60 percent with a read failure at LBA `246502720`, and `Current_Pending_Sector` increased from one to two. I retained the full sanitized result before removing its unused partition metadata. The disk remains installed only as failed hardware and is not a Proxmox storage target.

## Memory Modules

![Two SK hynix SO-DIMM memory modules](Images/image-1776104321961.jpg)

The retained photo shows two SK hynix SO-DIMM modules from the node hardware.

| Node | Slot 1 | Slot 2 | Installed | Usable memory |
| --- | --- | --- | ---: | ---: |
| blue-server | Samsung `M471A5644EB0-CPB`, 2 GB DDR4-2133 | SK Hynix `HMA851S6AFR6N-UH`, 4 GB DDR4-2400 at 2133 MT/s | 6 GB | 5.68 GiB |
| green-server | Micron `8ATF1G64HZ-2G6E1`, 8 GB DDR4-2667 | SK Hynix `HMA81GS6CJR8N-VK`, 8 GB DDR4-2667 | 16 GB | 15.46 GiB |

I moved Blue's former 8 GB module to Green and installed the 2 GB module in Blue. The live SMBIOS and Proxmox memory readbacks produced the values above.
