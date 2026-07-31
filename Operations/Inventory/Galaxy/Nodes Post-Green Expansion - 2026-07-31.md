# Galaxy Nodes Post-Green Expansion Snapshot

**Created:** 2026-07-31  
**Last updated:** 2026-07-31  
**Snapshot date:** 2026-07-31

I carried the complete node and physical-storage inventory forward after Green joined Galaxy, Blue moved to 6 GB installed memory, and Green moved to 16 GB. The live cluster reported five expected votes, five total votes, quorum 3, and `Quorate`. It contained 19 guest records, 12 running guests, and five cluster storage definitions.

Galaxy has five nodes with 30 physical CPU cores, 38 hardware threads, and 114.78 GiB of usable memory. It has five NVMe boot devices, two SATA SSDs, one 1.82 TiB ZFS HDD, one 931.51 GiB media HDD, one unused 465.76 GiB Blue HDD, and one blank but failed 298.09 GiB Green HDD.

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
| purple-server | `/dev/sda` | SSD | Samsung SSD 850 EVO 250GB | 232.89 GiB | `ssd-lvm2` LVM-thin; VM 122 |
| red-server | `/dev/nvme0n1` | NVMe | Samsung MZVLB256HAHQ-000L7 | 238.47 GiB | Proxmox boot |
| red-server | `/dev/sda` | HDD | Seagate ST1000LM035-1RK172 | 931.51 GiB | CT 842 `/data` through a host ext4 bind mount |

Green's NVMe was the only installation target in the PXE result. Its `/dev/nvme0n1p3` is the only LVM PV on Green. The Hitachi HDD has no Proxmox storage, LVM, ZFS, swap, filesystem, mount, partition-table type, or `fstab` reference.

Green's Hitachi extended test stopped at 60 percent with a read failure at LBA `246502720`. `Current_Pending_Sector` increased from one to two while reallocated and offline-uncorrectable counts remained zero. The top-level assessment still said `PASSED`, so I classified the disk from the completed self-test and kept it out of service.

Blue's WDC finished its own extended test at 11:32 EDT the same day with no failing LBA and all four critical counters at 0. This snapshot carries that completed result rather than the in-flight status it was first captured with. Blue's disk also holds an empty GPT from a 09:10 EDT Proxmox `diskinit`, which is a partition table with zero partitions and no filesystem.

## Memory modules

| Node | Slot 1 | Slot 2 | Installed | Proxmox usable |
| --- | --- | --- | ---: | ---: |
| blue-server | Samsung `M471A5644EB0-CPB`, 2 GB DDR4-2133 | SK Hynix `HMA851S6AFR6N-UH`, 4 GB DDR4-2400 at 2133 MT/s | 6 GB | 5.68 GiB |
| green-server | Micron `8ATF1G64HZ-2G6E1`, 8 GB DDR4-2667 | SK Hynix `HMA81GS6CJR8N-VK`, 8 GB DDR4-2667 | 16 GB | 15.46 GiB |

I moved Blue's former 8 GB module to Green and installed the 2 GB module in Blue. The rows record the live SMBIOS module identities and the memory exposed to Proxmox.
