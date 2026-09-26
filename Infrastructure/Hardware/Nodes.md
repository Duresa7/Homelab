# Galaxy Node Spec Sheet

**Created:** 2026-07-08  
**Last updated:** 2026-09-25

I run Galaxy as five nodes with 30 physical CPU cores, 38 hardware threads, 114.78 GiB of usable memory, five NVMe boot devices, two SATA SSDs, and four SATA HDDs. Blue's 465.76 GiB HDD is unused after passing its extended test. Green's 298.09 GiB HDD is blank but failed its extended test and must not receive data. Green also has unresolved host memory errors from 2026-09-20 and holds no guests. The memory and storage-pool figures below are the 2026-09-24 readback through `pvesh`.

## Recent changes

- 2026-09-24: I read memory and storage back from all five nodes. `hddpool-1` stood at 70.7% against 82.46% on 2026-09-06, and no record explains the roughly 200 GiB it gave back.
- 2026-09-23: I moved VM 103 `win11-dev` and its volumes from Green to Grey's `local-lvm`, leaving Green's pool empty. [Migration record](../Compute/Galaxy/Documentation/Change%20Records/win11-dev%20Grey%20Migration%20-%202026-09-23.md).
- 2026-09-20: Green's first Windows install crashed and an online host memory test produced 25 failure lines. [Memory-failure record](../Compute/Galaxy/Documentation/Troubleshooting/Memory%20Test%20Failures%20on%20green-server%20-%202026-09-20.md).

## Nodes

| Node | IP | CPU | Cores / Threads | Memory | Memory used (2026-09-24) | GPU | Physical storage | Power source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| blue-server | 192.168.70.12 | Intel Core i5-7500T @ 2.70GHz | 4 / 4 | 5.68 GiB | 2.99 GiB | Intel HD Graphics 630, integrated | 1x NVMe, 1x HDD | [UPS-02](Power.md) |
| green-server | 192.168.70.14 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | 1.91 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x HDD | Not reported |
| grey-server | 192.168.70.10 | AMD Ryzen 7 3700X | 8 / 16 | 62.72 GiB | 51.61 GiB | NVIDIA GeForce GTX 1080 Ti, discrete | 1x NVMe, 1x SSD, 1x HDD | [UPS-02](Power.md) |
| purple-server | 192.168.70.11 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | 11.68 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x SSD | Not reported |
| red-server | 192.168.70.13 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | 3.29 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x HDD | [UPS-02](Power.md) |

## Physical Storage

I verified the devices against all five nodes on 2026-08-04. The Used-by column follows the guest placement of 2026-09-24.

| Node | Device | Type | Model | Size | Used by |
| --- | --- | --- | --- | --- | --- |
| blue-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLW256HEHP-000L7 | 238.47 GiB | Proxmox boot, root, swap, `local-lvm`, and CTs 100, 104, 107 and 108 |
| blue-server | /dev/sda | HDD | WDC WD5000LPVX-08V0TT5 | 465.76 GiB | Unused; empty GPT, no filesystem or LVM; passed its extended SMART test |
| green-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLB256HAHQ-000L7 | 238.47 GiB | Proxmox boot, root, swap, and an empty `local-lvm` |
| green-server | /dev/sda | HDD | HITACHI HTS723232A7A364 | 298.09 GiB | Blank; extended test stopped with a read failure and two pending sectors; do not use |
| grey-server | /dev/nvme0n1 | NVMe | CT1000P310SSD8 | 931.51 GiB | Proxmox boot and `local-lvm`: VMs 102, 103 and 105 and CT 110's rootfs |
| grey-server | /dev/sda | SSD | CT2000BX500SSD1 | 1.82 TiB | `ssd-lvm1` LVM-thin: VMs 109, 200, 301, 302, 303 and 310 and templates 101, 300 and 9000 |
| grey-server | /dev/sdb | HDD | TOSHIBA_DT01ACA200 | 1.82 TiB | `hddpool-1` ZFS: CT 110's `/data` |
| purple-server | /dev/nvme0n1 | NVMe | THNSF5256GPUK TOSHIBA | 238.47 GiB | Proxmox boot and `local-lvm`: VMs 116, 121 and 401 |
| purple-server | /dev/sda | SSD | Samsung SSD 850 EVO 250GB | 232.89 GiB | `ssd-lvm2` LVM-thin, restricted to Purple; empty |
| red-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLB256HAHQ-000L7 | 238.47 GiB | Proxmox boot and `local-lvm`: CT 842's rootfs |
| red-server | /dev/sda | HDD | ST1000LM035-1RK172 | 931.51 GiB | CT 842 `/data` through a host ext4 bind mount |

Purple's boot device changed on 2026-07-25. The Samsung MZVLB256HAHQ-000L7 that shipped in it wore out at 169% of rated endurance, so I cloned it onto the Toshiba THNSF5256GPUK listed above and added the 850 EVO on the SATA port at the same time. On 2026-07-28 I configured the 850 EVO as `ssd-lvm2`, restricted the pool to Purple, and moved Kasm VM 122 onto it. The pool returned to 0.00 percent after I destroyed VM 122 and all of its volumes on 2026-08-19. Both drives and the retired Samsung are in the [drive inventory](Components/Drives/README.md); the swap is written up in [Purple Boot NVMe Replacement](../Compute/Galaxy/Documentation/Change%20Records/Purple%20Boot%20NVMe%20Replacement%20-%202026-07-25.md).

I added Blue's WDC HDD before the 2026-07-30 shutdown. It retained an older Proxmox VG named `pve`, which collided with Blue's live NVMe VG at the next boot. I verified the NVMe held the mounted root and all three guest volumes, then wiped the WDC partition table and signatures after confirming its old layout wasn't needed. The [duplicate VG troubleshooting record](../Compute/Galaxy/Documentation/Troubleshooting/Duplicate%20pve%20Volume%20Group%20on%20blue-server%20-%202026-07-30.md) records the repair.

That WDC disk then passed a full extended SMART read on 2026-07-31 at 23,215 power-on hours with zero reallocated, pending, offline-uncorrectable, and CRC-error sectors. It now carries an empty GPT written by a Proxmox `diskinit` task at 09:10 EDT the same day, so `wipefs` reports a `gpt` label where the 00:00 wipe had left none. It holds no partition, filesystem, or LVM PV.

I added Green's Hitachi HDD during the five-node expansion. Its extended SMART test stopped at 60 percent with a read failure at LBA `246502720`, and `Current_Pending_Sector` increased from one to two while reallocated and offline-uncorrectable counts stayed at zero. The top-level assessment still said `PASSED`, so I classified the disk from the completed self-test. I retained the full sanitized result before removing its unused partition metadata. The disk remains installed only as failed hardware and has no Proxmox storage, LVM, ZFS, swap, filesystem, mount, partition-table type, or `fstab` reference.

## Cluster Storage

**`pvesm status` answers for the node you ask.** Three of these storages are restricted to one node, so each reads `active` on its own node and `disabled` everywhere else. No `disable` flag is set on anything in `/etc/pve/storage.cfg`. Reading one node's output as the cluster's answer is how `ssd-lvm2` came to be recorded as disabled with no cause; it was never disabled. The table below reads each node's own storage.

From `pvesh get /nodes/<node>/storage` on 2026-09-24:

| Node | Storage | Type | Total | Used | Used % |
| --- | --- | --- | ---: | ---: | ---: |
| grey-server | `hddpool-1` | zfspool | 1,798.5 GiB | 1,271.8 GiB | 70.7% |
| grey-server | `ssd-lvm1` | lvmthin | 1,830.9 GiB | 200.8 GiB | 11.0% |
| grey-server | `local-lvm` | lvmthin | 793.8 GiB | 240.7 GiB | 30.3% |
| grey-server | `local` | dir | 93.9 GiB | 46.4 GiB | 49.4% |
| purple-server | `local-lvm` | lvmthin | 140.9 GiB | 40.0 GiB | 28.4% |
| purple-server | `ssd-lvm2` | lvmthin | 228.1 GiB | 0.0 GiB | 0.0% |
| purple-server | `local` | dir | 67.6 GiB | 8.3 GiB | 12.3% |
| blue-server | `local-lvm` | lvmthin | 141.2 GiB | 55.0 GiB | 39.0% |
| blue-server | `local` | dir | 67.7 GiB | 8.4 GiB | 12.4% |
| red-server | `local-lvm` | lvmthin | 141.2 GiB | 45.0 GiB | 31.9% |
| red-server | `local` | dir | 67.7 GiB | 8.5 GiB | 12.6% |
| green-server | `local-lvm` | lvmthin | 141.2 GiB | 0.0 GiB | 0.0% |
| green-server | `local` | dir | 67.7 GiB | 23.5 GiB | 34.7% |

`ssd-lvm2` is restricted to Purple by `nodes purple-server`, and `ssd-lvm1` and `hddpool-1` live on Grey. `local` and `local-lvm` are per-node storages. Purple's thin volumes are provisioned at 154.01 GiB against the 140.87 GiB pool, as I recorded when `alpha-prod-01` moved there on 2026-09-12, so a new allocation on Purple needs a capacity check first. [alpha-prod-01 Purple Migration](../Compute/Galaxy/Documentation/Change%20Records/alpha-prod-01%20Purple%20Migration%20-%202026-09-12.md).

`hddpool-1` read 80.08% on 2026-08-09 and 82.46% on 2026-09-06, which was Immich growth on `docker-main`'s `/data` mount. The drop to 70.7% by 2026-09-24 has no record.

`ssd-lvm2` has been empty since I destroyed Kasm VM 122 on 2026-08-19. The [purple 850 EVO SMART baseline](../../Archive/Platforms/Kasm%20Workspaces/Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/Purple%20850%20EVO%20SMART%20Baseline.md) remains the retained health record for the underlying disk.

## Memory Modules

![Two SK hynix SO-DIMM memory modules photographed on 2026-04-13](Images/SO-DIMM%20Pair%20-%202026-04-13.jpg)

The photo dates from 2026-04-13, before the 2026-07-31 module swap, and shows two SK hynix SO-DIMM modules. It does not show the current slot layout; the table below does.

| Node | Slot 1 | Slot 2 | Installed | Usable memory |
| --- | --- | --- | ---: | ---: |
| blue-server | Samsung `M471A5644EB0-CPB`, 2 GB DDR4-2133 | SK Hynix `HMA851S6AFR6N-UH`, 4 GB DDR4-2400 at 2133 MT/s | 6 GB | 5.68 GiB |
| green-server | Micron `8ATF1G64HZ-2G6E1`, 8 GB DDR4-2667 | SK Hynix `HMA81GS6CJR8N-VK`, 8 GB DDR4-2667 | 16 GB | 15.46 GiB |

I moved Blue's former 8 GB module to Green and installed the 2 GB module in Blue on 2026-07-31. The live SMBIOS and Proxmox memory readbacks produced the values above.

## Superseded Snapshots

- [Nodes Post-Green Expansion - 2026-07-31](../../Archive/Operations/Inventory/Galaxy/Snapshots/Nodes%20Post-Green%20Expansion%20-%202026-07-31.md), the five-node state this record was updated from
- [Nodes Post-Blue SATA Wipe - 2026-07-31](../../Archive/Operations/Inventory/Galaxy/Snapshots/Nodes%20Post-Blue%20SATA%20Wipe%20-%202026-07-31.md), the earlier four-node state before Green joined
- [Nodes Post-Kasm Build-Out - 2026-07-28](../../Archive/Operations/Inventory/Galaxy/Snapshots/Nodes%20Post-Kasm%20Build-Out%20-%202026-07-28.md), [Nodes - 2026-07-28](../../Archive/Operations/Inventory/Galaxy/Snapshots/Nodes%20-%202026-07-28.md), and [Nodes - 2026-07-27](../../Archive/Operations/Inventory/Galaxy/Snapshots/Nodes%20-%202026-07-27.md)
