# Galaxy Node Spec Sheet

**Created:** 2026-07-08  
**Last updated:** 2026-08-09

I run Galaxy as five nodes with 30 physical CPU cores, 38 hardware threads, 114.78 GiB of usable memory, five NVMe boot devices, two SATA SSDs, and four SATA HDDs. Blue's 465.76 GiB HDD is unused after passing its extended test. Green's 298.09 GiB HDD is blank but failed its extended test and must not receive data. I keep each model, capacity, management address, and reported UPS assignment separate.

I verified the node and physical-storage state against all five nodes on 2026-08-04. Quorum held at five votes.

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
| blue-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLW256HEHP-000L7 | 238.47 GiB | Proxmox boot, root, swap, `local-lvm`, and CTs 104/107/108 |
| blue-server | /dev/sda | HDD | WDC WD5000LPVX-08V0TT5 | 465.76 GiB | Unused; empty GPT, no filesystem or LVM; passed its extended SMART test |
| green-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLB256HAHQ-000L7 | 238.47 GiB | Proxmox boot, root, swap, and `local-lvm` |
| green-server | /dev/sda | HDD | HITACHI HTS723232A7A364 | 298.09 GiB | Blank; extended test stopped with a read failure and two pending sectors; do not use |
| grey-server | /dev/nvme0n1 | NVMe | CT1000P310SSD8 | 931.51 GiB | Proxmox boot |
| grey-server | /dev/sda | SSD | CT2000BX500SSD1 | 1.82 TiB | `ssd-lvm1` LVM-thin |
| grey-server | /dev/sdb | HDD | TOSHIBA_DT01ACA200 | 1.82 TiB | `hddpool-1` ZFS |
| purple-server | /dev/nvme0n1 | NVMe | THNSF5256GPUK TOSHIBA | 238.47 GiB | Proxmox boot |
| purple-server | /dev/sda | SSD | Samsung SSD 850 EVO 250GB | 232.89 GiB | `ssd-lvm2` LVM-thin, restricted to Purple; VM and LXC images; VM 122 |
| red-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLB256HAHQ-000L7 | 238.47 GiB | Proxmox boot |
| red-server | /dev/sda | HDD | ST1000LM035-1RK172 | 931.51 GiB | CT 842 `/data` through host ext4 bind mount |

Purple's boot device changed on 2026-07-25. The Samsung MZVLB256HAHQ-000L7 that shipped in it wore out at 169% of rated endurance, so I cloned it onto the Toshiba THNSF5256GPUK listed above & added the 850 EVO on the SATA port at the same time. On 2026-07-28 I configured the 850 EVO as `ssd-lvm2`, restricted the pool to Purple, and moved Kasm VM 122 onto it. On 2026-08-04 the pool was active on Purple at 69.90 percent of 228.11 GiB. Both drives and the retired Samsung are in the [drive inventory](Components/Drives/README.md); the swap is written up in [Purple Boot NVMe Replacement](../Compute/Galaxy/Documentation/Change%20Records/Purple%20Boot%20NVMe%20Replacement%20-%202026-07-25.md).

I added Blue's WDC HDD before the 2026-07-30 shutdown. It retained an older Proxmox VG named `pve`, which collided with Blue's live NVMe VG at the next boot. I verified the NVMe held the mounted root and all three guest volumes, then wiped the WDC partition table and signatures after confirming its old layout wasn't needed. The [duplicate VG troubleshooting record](../Compute/Galaxy/Documentation/Troubleshooting/Duplicate%20pve%20Volume%20Group%20on%20blue-server%20-%202026-07-30.md) records the repair.

That WDC disk then passed a full extended SMART read on 2026-07-31 at 23,215 power-on hours with zero reallocated, pending, offline-uncorrectable, & CRC-error sectors. It now carries an empty GPT written by a Proxmox `diskinit` task at 09:10 EDT the same day, so `wipefs` reports a `gpt` label where the 00:00 wipe had left none. It holds no partition, filesystem, or LVM PV.

I added Green's Hitachi HDD during the five-node expansion. Its extended SMART test stopped at 60 percent with a read failure at LBA `246502720`, and `Current_Pending_Sector` increased from one to two while reallocated and offline-uncorrectable counts stayed at zero. The top-level assessment still said `PASSED`, so I classified the disk from the completed self-test. I retained the full sanitized result before removing its unused partition metadata. The disk remains installed only as failed hardware and has no Proxmox storage, LVM, ZFS, swap, filesystem, mount, partition-table type, or `fstab` reference.

## Cluster Storage

**`pvesm status` answers for the node you ask.** Three of these storages are restricted to one node, so each reads `active` on its own node and `disabled` everywhere else. There is no cluster-wide view, and no `disable` flag is set on anything in `/etc/pve/storage.cfg`. Reading one node's output as the cluster's answer is how `ssd-lvm2` came to be recorded as disabled with no cause; it was never disabled.

From `grey-server` on 2026-08-09:

| Storage | Type | Status | Total | Used |
| --- | --- | --- | ---: | ---: |
| `hddpool-1` | zfspool | active | 1.76 TiB | 80.08% |
| `local` | dir | active | 93.93 GiB | 34.15% |
| `local-lvm` | lvmthin | active | 793.79 GiB | 11.47% |
| `ssd-lvm1` | lvmthin | active | 1.79 TiB | 13.05% |
| `ssd-lvm2` | lvmthin | disabled | Not reported | Not reported |

From `purple-server` the same day, which shows the pattern reversing:

| Storage | Type | Status | Total | Used |
| --- | --- | --- | ---: | ---: |
| `hddpool-1` | zfspool | disabled | Not reported | Not reported |
| `local` | dir | active | 67.61 GiB | 10.05% |
| `local-lvm` | lvmthin | active | 140.87 GiB | 0.00% |
| `ssd-lvm1` | lvmthin | disabled | Not reported | Not reported |
| `ssd-lvm2` | lvmthin | active | 228.11 GiB | 69.90% |

`ssd-lvm2` is restricted to Purple by `nodes purple-server`, and `ssd-lvm1` and `hddpool-1` both live on Grey, which is why each side reports the other's pools as disabled. `local` and `local-lvm` are per-node storages, so their capacities differ between the two tables rather than disagreeing.

`ssd-lvm2` backs Kasm VM 122 and stood at 69.90 percent data and 3.06 percent metadata on 2026-08-04, against the 80 percent hard stop. The [purple 850 EVO SMART baseline](../../Platforms/Kasm%20Workspaces/Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/Purple%20850%20EVO%20SMART%20Baseline.md) shows the underlying disk healthy, with 15 normalized wear against a stop condition of 10.

The 2026-08-09 `ssd-lvm1` reading follows the deletion of retired CT 105 and its 100 GiB root volume. The pool read 15.72 percent immediately before the deletion and 13.05 percent immediately afterward; the [retirement record](../Compute/Galaxy/Documentation/Change%20Records/AI%20Bravo%2002%20Retirement%20-%202026-08-09.md) records the guarded removal.

## Memory Modules

![Two SK hynix SO-DIMM memory modules](Images/image-1776104321961.jpg)

The retained photo shows two SK hynix SO-DIMM modules from the node hardware.

| Node | Slot 1 | Slot 2 | Installed | Usable memory |
| --- | --- | --- | ---: | ---: |
| blue-server | Samsung `M471A5644EB0-CPB`, 2 GB DDR4-2133 | SK Hynix `HMA851S6AFR6N-UH`, 4 GB DDR4-2400 at 2133 MT/s | 6 GB | 5.68 GiB |
| green-server | Micron `8ATF1G64HZ-2G6E1`, 8 GB DDR4-2667 | SK Hynix `HMA81GS6CJR8N-VK`, 8 GB DDR4-2667 | 16 GB | 15.46 GiB |

I moved Blue's former 8 GB module to Green and installed the 2 GB module in Blue on 2026-07-31. The live SMBIOS and Proxmox memory readbacks produced the values above.

## Superseded Snapshots

- [Nodes Post-Green Expansion - 2026-07-31](../../Operations/Inventory/Galaxy/Nodes%20Post-Green%20Expansion%20-%202026-07-31.md), the five-node state this record was updated from
- [Nodes Post-Blue SATA Wipe - 2026-07-31](../../Operations/Inventory/Galaxy/Nodes%20Post-Blue%20SATA%20Wipe%20-%202026-07-31.md), the earlier four-node state before Green joined
- [Nodes Post-Kasm Build-Out - 2026-07-28](../../Operations/Inventory/Galaxy/Nodes%20Post-Kasm%20Build-Out%20-%202026-07-28.md), [Nodes - 2026-07-28](../../Operations/Inventory/Galaxy/Nodes%20-%202026-07-28.md), and [Nodes - 2026-07-27](../../Operations/Inventory/Galaxy/Nodes%20-%202026-07-27.md)
