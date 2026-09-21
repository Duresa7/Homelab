# Galaxy Node Spec Sheet

**Created:** 2026-07-08  
**Last updated:** 2026-09-21

On 2026-09-12 I retired `game-01` from active service. I subsequently deleted CT 123 and its 80 GiB `local-lvm:vm-123-disk-0` volume, including the game data. The guest and disk are absent. Green’s pool was empty after that deletion. On 2026-09-20 I allocated VM 103 `win11-dev` with 4 vCPUs, 8 GiB RAM and a 120 GiB system disk. Its first Windows installation crashed and an 8 GiB online host memory test produced 25 failure lines. I chose to continue on this host and completed Windows 11 Pro and SSH on 2026-09-21. VM 103 now runs with `onboot=1`; the host memory fault remains unresolved. At 3:25:56 AM Eastern on 2026-09-21 the pool used 34,193,238 KiB (23.09%), with 113,893,545 KiB available. [Completion record](../Compute/Galaxy/Documentation/Change%20Records/win11-dev%20Completion%20-%202026-09-21.md). [Memory-failure record](../Compute/Galaxy/Documentation/Troubleshooting/Memory%20Test%20Failures%20on%20green-server%20-%202026-09-20.md).

I run Galaxy as five nodes with 30 physical CPU cores, 38 hardware threads, 114.78 GiB of usable memory, five NVMe boot devices, two SATA SSDs, and four SATA HDDs. Blue's 465.76 GiB HDD is unused after passing its extended test. Green's 298.09 GiB HDD is blank but failed its extended test and must not receive data. I keep each model, capacity, management address, and reported UPS assignment separate.

I verified the node and physical-storage state against all five nodes on 2026-08-04. Quorum held at five votes.

On 2026-09-11 I replaced app-01's 200 GiB system disk on Grey's `ssd-lvm1` with a 64 GiB volume and removed the old disk. Guest placement and physical hardware are unchanged. The [change record](../Compute/Galaxy/Documentation/Change%20Records/app-01%2064%20GiB%20Boot%20Disk%20Replacement%20-%202026-09-11.md) holds verification.

On 2026-09-11 I subsequently moved VM 116 `app-01` and VM 121 `edge-01` from Grey to Purple's NVMe-backed `local-lvm`. Their system disks total 94 GiB provisioned, with two 4 MiB EFI volumes. At about 3:29 AM Eastern the pool used 21,950,307 KiB (14.86%) with 125,763,740 KiB available, Purple had 6,679 MiB available memory, and its SATA `ssd-lvm2` remained empty. Both guests run on Purple and their old volumes are absent from Grey. [Migration record](../Compute/Galaxy/Documentation/Change%20Records/app-01%20and%20edge-01%20Purple%20Migration%20-%202026-09-11.md).

On 2026-09-12 I moved CT 100 `ansible-01` from Grey's `ssd-lvm1` to Blue's NVMe-backed `local-lvm`. At 3:38 PM Eastern, Blue had 2,942 MiB available memory and its thin pool used 34.08%, with 97,618,808 KiB available. The source volume is absent from Grey. [Migration record](../Compute/Galaxy/Documentation/Change%20Records/ansible-01%20Blue%20Migration%20-%202026-09-12.md).

On 2026-09-12 I moved VM 401 `alpha-prod-01` from Grey to Purple's NVMe-backed `local-lvm`. After startup, Purple had 3,529 MiB available memory and its thin pool was 19.50% used, with 118,909,808 KiB available. Both source volumes are absent from Grey. Provisioned thin volumes total 154.01 GiB against a roughly 140.87 GiB pool, so future allocation needs capacity monitoring. [Migration record](../Compute/Galaxy/Documentation/Change%20Records/alpha-prod-01%20Purple%20Migration%20-%202026-09-12.md).

## Nodes
| Node | IP | CPU | Cores / Threads | Memory | GPU | Physical storage | Power source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| blue-server | 192.168.70.12 | Intel Core i5-7500T @ 2.70GHz | 4 / 4 | 5.68 GiB | Intel HD Graphics 630, integrated | 1x NVMe, 1x HDD | [UPS-02](Power.md) |
| green-server | 192.168.70.14 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x HDD | Not reported |
| grey-server | 192.168.70.10 | AMD Ryzen 7 3700X | 8 / 16 | 62.72 GiB | NVIDIA GeForce GTX 1080 Ti, discrete | 1x NVMe, 1x SSD, 1x HDD | [UPS-02](Power.md) |
| purple-server | 192.168.70.11 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x SSD | Not reported |
| red-server | 192.168.70.13 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x HDD | [UPS-02](Power.md) |

On 2026-09-08 I moved VM 105 `ubuntu-dev` onto Grey's NVMe-backed `local-lvm` and removed its two unused SATA SSD source volumes. `ssd-lvm1` then reported 231,147,287 KiB used (12.04%), about 62.4 GiB less than immediately before deletion. The [storage move record](../Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%20NVMe%20Storage%20Move%20-%202026-09-08.md) holds the disk identities and verification.

On 2026-09-10 I set VM 105 `ubuntu-dev` on Grey to 12 GiB pending, leaving its running allocation at 16 GiB. I did not restart anything, so the 4 GiB reduction has not yet released host capacity. The [memory assessment and change record](../Compute/Galaxy/Documentation/Change%20Records/ubuntu-dev%20Memory%20Assessment%20-%202026-09-10.md) holds the verification.

## Physical Storage
| Node | Device | Type | Model | Size | Used by |
| --- | --- | --- | --- | --- | --- |
| blue-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLW256HEHP-000L7 | 238.47 GiB | Proxmox boot, root, swap, `local-lvm`, and CTs 100/104/107/108 |
| blue-server | /dev/sda | HDD | WDC WD5000LPVX-08V0TT5 | 465.76 GiB | Unused; empty GPT, no filesystem or LVM; passed its extended SMART test |
| green-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLB256HAHQ-000L7 | 238.47 GiB | Proxmox boot, root, swap, and `local-lvm`; VM 103 running; host memory errors remain unresolved |
| green-server | /dev/sda | HDD | HITACHI HTS723232A7A364 | 298.09 GiB | Blank; extended test stopped with a read failure and two pending sectors; do not use |
| grey-server | /dev/nvme0n1 | NVMe | CT1000P310SSD8 | 931.51 GiB | Proxmox boot and `local-lvm`, including VM 105 system and EFI disks |
| grey-server | /dev/sda | SSD | CT2000BX500SSD1 | 1.82 TiB | `ssd-lvm1` LVM-thin |
| grey-server | /dev/sdb | HDD | TOSHIBA_DT01ACA200 | 1.82 TiB | `hddpool-1` ZFS |
| purple-server | /dev/nvme0n1 | NVMe | THNSF5256GPUK TOSHIBA | 238.47 GiB | Proxmox boot |
| purple-server | /dev/sda | SSD | Samsung SSD 850 EVO 250GB | 232.89 GiB | `ssd-lvm2` LVM-thin, restricted to Purple; currently empty |
| red-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLB256HAHQ-000L7 | 238.47 GiB | Proxmox boot |
| red-server | /dev/sda | HDD | ST1000LM035-1RK172 | 931.51 GiB | CT 842 `/data` through host ext4 bind mount |

Purple's boot device changed on 2026-07-25. The Samsung MZVLB256HAHQ-000L7 that shipped in it wore out at 169% of rated endurance, so I cloned it onto the Toshiba THNSF5256GPUK listed above & added the 850 EVO on the SATA port at the same time. On 2026-07-28 I configured the 850 EVO as `ssd-lvm2`, restricted the pool to Purple, and moved Kasm VM 122 onto it. The pool returned to 0.00 percent after I destroyed VM 122 and all of its volumes on 2026-08-19. Both drives and the retired Samsung are in the [drive inventory](Components/Drives/README.md); the swap is written up in [Purple Boot NVMe Replacement](../Compute/Galaxy/Documentation/Change%20Records/Purple%20Boot%20NVMe%20Replacement%20-%202026-07-25.md).

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

From `purple-server` on 2026-08-19, after destroying VM 122:

| Storage | Type | Status | Total | Used |
| --- | --- | --- | ---: | ---: |
| `hddpool-1` | zfspool | disabled | Not reported | Not reported |
| `local` | dir | active | 67.61 GiB | 10.05% |
| `local-lvm` | lvmthin | active | 140.87 GiB | 0.00% |
| `ssd-lvm1` | lvmthin | disabled | Not reported | Not reported |
| `ssd-lvm2` | lvmthin | active | 228.11 GiB | 0.00% |

`ssd-lvm2` is restricted to Purple by `nodes purple-server`, and `ssd-lvm1` and `hddpool-1` both live on Grey, which is why each side reports the other's pools as disabled. `local` and `local-lvm` are per-node storages, so their capacities differ between the two tables rather than disagreeing.

I re-read both nodes on 2026-09-06 during the documentation audit. The shape is unchanged; the figures below are the current usage.

From `grey-server` on 2026-09-06:

| Storage | Type | Status | Total | Used |
| --- | --- | --- | ---: | ---: |
| `hddpool-1` | zfspool | active | 1.76 TiB | 82.46% |
| `local` | dir | active | 93.93 GiB | 43.40% |
| `local-lvm` | lvmthin | active | 793.79 GiB | 11.37% |
| `ssd-lvm1` | lvmthin | active | 1.79 TiB | 13.47% |
| `ssd-lvm2` | lvmthin | disabled | Not reported | Not reported |

From `purple-server` on 2026-09-06:

| Storage | Type | Status | Total | Used |
| --- | --- | --- | ---: | ---: |
| `hddpool-1` | zfspool | disabled | Not reported | Not reported |
| `local` | dir | active | 67.61 GiB | 12.31% |
| `local-lvm` | lvmthin | active | 140.87 GiB | 0.00% |
| `ssd-lvm1` | lvmthin | disabled | Not reported | Not reported |
| `ssd-lvm2` | lvmthin | active | 228.11 GiB | 0.00% |

`hddpool-1` has moved from 80.08 to 82.46 percent since 2026-08-09, which is Immich growth on `docker-main`'s `/data` mount. `ssd-lvm2` is still empty. The per-node `local-lvm` figures on the other three nodes were blue 26.00, red 31.73, and green 8.58 percent.

`ssd-lvm2` is empty after the Kasm retirement. `pvesm list ssd-lvm2 --vmid 122` returned no volumes and `pvesm status --storage ssd-lvm2` reported 0.00 percent used on 2026-08-19. The [purple 850 EVO SMART baseline](../../Archive/Platforms/Kasm%20Workspaces/Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/Purple%20850%20EVO%20SMART%20Baseline.md) remains the retained health record for the underlying disk.

The 2026-08-09 `ssd-lvm1` reading follows the deletion of retired CT 105 and its 100 GiB root volume. The pool read 15.72 percent immediately before the deletion and 13.05 percent immediately afterward; the [retirement record](../../Archive/Infrastructure/Compute/Galaxy/Documentation/Change%20Records/AI%20Bravo%2002%20Retirement%20-%202026-08-09.md) records the guarded removal.

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
