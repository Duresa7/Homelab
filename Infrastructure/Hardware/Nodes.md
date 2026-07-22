# Galaxy Node Spec Sheet

**Created:** 2026-07-08  
**Last updated:** 2026-07-22

I run Galaxy as four nodes with 24 physical CPU cores, 105.21 GiB of memory, four NVMe boot devices, one 1.82 TiB SSD, one 1.82 TiB ZFS disk, & one 931.51 GiB media HDD. I keep each model, capacity, management address, & reported UPS assignment separate.

## Nodes
| Node | IP | CPU | Cores / Threads | Memory | GPU | Physical storage | Power source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| blue-server | 192.168.70.12 | Intel Core i5-7500T @ 2.70GHz | 4 / 4 | 11.57 GiB | Intel HD Graphics 630, integrated | 1x NVMe | [UPS-02](Power.md) |
| grey-server | 192.168.70.10 | AMD Ryzen 7 3700X | 8 / 16 | 62.72 GiB | NVIDIA GeForce GTX 1080 Ti, discrete | 1x NVMe, 1x SSD, 1x HDD | [UPS-02](Power.md) |
| purple-server | 192.168.70.11 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe | Not reported |
| red-server | 192.168.70.13 | Intel Core i5-8500T @ 2.10GHz | 6 / 6 | 15.46 GiB | Intel UHD Graphics 630, integrated | 1x NVMe, 1x HDD | [UPS-01; also reported on UPS-02](Power.md) |

## Physical Storage
| Node | Device | Type | Model | Size | Used by |
| --- | --- | --- | --- | --- | --- |
| blue-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLW256HEHP-000L7 | 238.47 GiB | BIOS boot |
| grey-server | /dev/nvme0n1 | NVMe | CT1000P310SSD8 | 931.51 GiB | BIOS boot |
| grey-server | /dev/sda | SSD | CT2000BX500SSD1 | 1.82 TiB | LVM |
| grey-server | /dev/sdb | HDD | TOSHIBA_DT01ACA200 | 1.82 TiB | ZFS |
| purple-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLB256HAHQ-000L7 | 238.47 GiB | BIOS boot |
| red-server | /dev/nvme0n1 | NVMe | SAMSUNG MZVLB256HAHQ-000L7 | 238.47 GiB | BIOS boot |
| red-server | /dev/sda | HDD | ST1000LM035-1RK172 | 931.51 GiB | CT 842 `/data` through host ext4 bind mount |

## Memory Modules

![Two SK hynix SO-DIMM memory modules](Images/image-1776104321961.jpg)

The retained photo shows two SK hynix SO-DIMM modules from the node hardware.
