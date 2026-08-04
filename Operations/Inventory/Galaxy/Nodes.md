# Galaxy Nodes

**Created:** 2026-08-04  
**Last updated:** 2026-08-04

The current node and physical-storage record for Galaxy. This is the living file: I edit it forward, and the dated `Nodes ...` files beside it are superseded snapshots. It exists because there wasn't one until 2026-08-04, which left the current answer split between two same-day 2026-07-31 snapshots, one of which predates Green joining and describes a four-node cluster.

Verified against all five nodes on 2026-08-04. Galaxy has five nodes with 30 physical cores, 38 hardware threads, and 114.78 GiB of usable memory. Quorum holds at five votes.

## Nodes

| Node | IP | CPU | Cores / Threads | Memory | GPU | Physical storage | Power source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| blue-server | 192.168.70.12 | Intel Core i5-7500T @ 2.70GHz | 4 / 4 | 5.68 GiB | Intel HD Graphics 630, integrated | 1x NVMe, 1x HDD | [UPS-02](../../../Infrastructure/Hardware/Power.md) |
| green-server | 192.168.70.14 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x HDD | Not reported |
| grey-server | 192.168.70.10 | AMD Ryzen 7 3700X | 8 / 16 | 62.72 GiB | NVIDIA GeForce GTX 1080 Ti, discrete | 1x NVMe, 1x SSD, 1x HDD | [UPS-02](../../../Infrastructure/Hardware/Power.md) |
| purple-server | 192.168.70.11 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x SSD | Not reported |
| red-server | 192.168.70.13 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x HDD | [UPS-01; also reported on UPS-02](../../../Infrastructure/Hardware/Power.md) |

## Physical storage

| Node | Device | Type | Model | Size | Used by |
| --- | --- | --- | --- | --- | --- |
| blue-server | `/dev/nvme0n1` | NVMe | Samsung MZVLW256HEHP-000L7 | 238.47 GiB | Proxmox boot, root, swap, `local-lvm`, and CTs 104/107/108 |
| blue-server | `/dev/sda` | HDD | WDC WD5000LPVX-08V0TT5 | 465.76 GiB | Unused; empty GPT, no filesystem or LVM; passed its extended SMART test |
| green-server | `/dev/nvme0n1` | NVMe | Samsung MZVLB256HAHQ-000L7 | 238.47 GiB | Proxmox boot, root, swap, and `local-lvm` |
| green-server | `/dev/sda` | HDD | Hitachi HTS723232A7A364 | 298.09 GiB | Blank; extended test stopped with a read failure and two pending sectors; do not use |
| grey-server | `/dev/nvme0n1` | NVMe | Crucial CT1000P310SSD8 | 931.51 GiB | Proxmox boot |
| grey-server | `/dev/sda` | SSD | Crucial CT2000BX500SSD1 | 1.82 TiB | `ssd-lvm1` LVM-thin |
| grey-server | `/dev/sdb` | HDD | Toshiba DT01ACA200 | 1.82 TiB | `hddpool-1` ZFS |
| purple-server | `/dev/nvme0n1` | NVMe | Toshiba THNSF5256GPUK | 238.47 GiB | Proxmox boot |
| purple-server | `/dev/sda` | SSD | Samsung SSD 850 EVO 250GB | 232.89 GiB | `ssd-lvm2` LVM-thin, currently disabled |
| red-server | `/dev/nvme0n1` | NVMe | Samsung MZVLB256HAHQ-000L7 | 238.47 GiB | Proxmox boot |
| red-server | `/dev/sda` | HDD | Seagate ST1000LM035-1RK172 | 931.51 GiB | CT 842 `/data` through a host ext4 bind mount |

## Cluster storage

`pvesm status` on 2026-08-04:

| Storage | Type | Status | Total | Used |
| --- | --- | --- | ---: | ---: |
| `hddpool-1` | zfspool | active | 1.76 TiB | 78.95% |
| `local` | dir | active | 93.93 GiB | 34.16% |
| `local-lvm` | lvmthin | active | 793.79 GiB | 11.43% |
| `ssd-lvm1` | lvmthin | active | 1.79 TiB | 12.69% |
| `ssd-lvm2` | lvmthin | disabled | Not reported | Not reported |

`ssd-lvm2` was active on 2026-07-31 backing Kasm VM 122 on purple. It reports `disabled` as of 2026-08-04 and returns no capacity. I have not established when or why it was disabled, and it is the one open question on this record. The [purple 850 EVO SMART baseline](../../../Platforms/Kasm%20Workspaces/Evidence/Kasm%20Session%20Isolation%20-%202026-07-28/Logs/Purple%20850%20EVO%20SMART%20Baseline.md) shows the underlying disk healthy, with 15 normalized wear against a stop condition of 10, so the disk is not the reason.

## Two disks deliberately out of service

Green's Hitachi extended test stopped at 60 percent with a read failure at LBA `246502720`, and `Current_Pending_Sector` rose from one to two while reallocated and offline-uncorrectable counts stayed at zero. The top-level assessment still said `PASSED`, so I classified the disk from the completed self-test rather than the summary line and kept it out of service. It carries no Proxmox storage, LVM, ZFS, swap, filesystem, mount, partition-table type, or `fstab` reference.

Blue's WDC passed its own extended test on 2026-07-31 with no failing LBA and all four critical counters at zero. It holds an empty GPT from a Proxmox `diskinit`, which is a partition table with zero partitions and no filesystem, and no workload uses it yet.

## Memory modules

| Node | Slot 1 | Slot 2 | Installed | Proxmox usable |
| --- | --- | --- | ---: | ---: |
| blue-server | Samsung `M471A5644EB0-CPB`, 2 GB DDR4-2133 | SK Hynix `HMA851S6AFR6N-UH`, 4 GB DDR4-2400 at 2133 MT/s | 6 GB | 5.68 GiB |
| green-server | Micron `8ATF1G64HZ-2G6E1`, 8 GB DDR4-2667 | SK Hynix `HMA81GS6CJR8N-VK`, 8 GB DDR4-2667 | 16 GB | 15.46 GiB |

I moved Blue's former 8 GB module to Green and installed the 2 GB module in Blue on 2026-07-31. The rows record the live SMBIOS module identities and the memory Proxmox exposes.

## Superseded snapshots

- [Nodes Post-Green Expansion - 2026-07-31](Nodes%20Post-Green%20Expansion%20-%202026-07-31.md), the five-node state this file was built from
- [Nodes Post-Blue SATA Wipe - 2026-07-31](Nodes%20Post-Blue%20SATA%20Wipe%20-%202026-07-31.md), same date but earlier: four nodes, before Green joined
- [Nodes Post-Kasm Build-Out - 2026-07-28](Nodes%20Post-Kasm%20Build-Out%20-%202026-07-28.md), [Nodes - 2026-07-28](Nodes%20-%202026-07-28.md), [Nodes - 2026-07-27](Nodes%20-%202026-07-27.md)
