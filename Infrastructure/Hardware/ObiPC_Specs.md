# PC Specifications: ObiPC

**Created:** 2026-09-11  
**Last updated:** 2026-09-11

ObiPC is the first physical end-user workstation on the `ad.alphasecunited.com` domain. It has an 8-core Ryzen 7 7700X, 32 GB of DDR5, an RTX 3070, a 1 TB and a 500 GB NVMe drive, and a 2.5 Gbps Ethernet adapter. Read from the machine over SSH on 2026-09-11.

## System Overview

| Property | Value |
|---|---|
| Computer Name | `ObiPC` |
| Role | End-user workstation, domain member in `OU=Standard,OU=Workstations` |
| Network | Secure Client, VLAN 60, DHCP, `192.168.60.102` at the time of the join |
| Manufacturer | ASUS |
| Model | System Product Name (custom build) |
| System Type | x64-based PC |

## Operating System

| Property | Value |
|---|---|
| OS | Microsoft Windows 11 Pro, 25H2, build 26200 |
| Installed | 2026-09-11 |
| Activation | Licensed |
| Firmware | UEFI, Secure Boot on since 2026-09-11 (Standard mode, Microsoft keys); off at install |
| TPM | AMD firmware TPM 2.0, version 6.32 |

## Processor (CPU)

| Property | Value |
|---|---|
| Model | AMD Ryzen 7 7700X 8-Core Processor |
| Cores | 8 |
| Logical Processors | 16 |
| Max Clock Speed | 4501 MHz |

## Memory (RAM)

**Total Installed:** 32 GB (31.16 GB usable)

| Slot | Manufacturer | Part Number | Capacity | Configured Speed |
|---|---|---|---|---|
| DIMM 1 | G.Skill | F5-6000J3636F16G | 16 GB | 4800 MHz |
| DIMM 2 | G.Skill | F5-6000J3636F16G | 16 GB | 4800 MHz |

Both modules report the same slot label to Windows; the second row is the second module. The kit is rated for 6000 MHz and runs at 4800, so an EXPO profile is not enabled in the BIOS.

## Graphics (GPU)

| Adapter | Notes |
|---|---|
| NVIDIA GeForce RTX 3070 | Discrete. Windows reports 4 GB of adapter memory, which is the 32-bit WMI cap, not the card's 8 GB. Driver 32.0.16.1074 |
| AMD Radeon Graphics | Integrated in the 7700X |

## Motherboard & BIOS

| Property | Value |
|---|---|
| Board | ASUS TUF GAMING B650-PLUS WIFI |
| BIOS | American Megatrends 3201, 2025-01-10 |

## Storage

| Disk | Capacity | Type | Bus | Health | Use |
|---|---|---|---|---|---|
| Samsung SSD 980 1TB | 932 GB | SSD | NVMe | Healthy | `C:`, Windows, 867 GB free after install |
| Crucial P310 500GB (`CT500P310SSD8`) | 466 GB | SSD | NVMe | Healthy | `D:` `Storage`, empty |

## Network

| Adapter | Description | Link | State |
|---|---|---|---|
| Ethernet | Realtek Gaming 2.5GbE Family Controller | 2.5 Gbps | Up, the domain-facing connection |
| Wi-Fi | Realtek 8852BE Wireless LAN WiFi 6 | none | Disconnected |

## Management

OpenSSH Server, key only, reached as `local-obipc` from SSH Manager as server `obipc`. The local account's password is in my password manager; the built-in `Administrator` password is managed by Windows LAPS and retrieved with `Get-LapsADPassword -Identity OBIPC -AsPlainText`. The build is recorded in [ObiPC Workstation Join - 2026-09-11](../../Platforms/Active%20Directory/Documentation/Change%20Records/ObiPC%20Workstation%20Join%20-%202026-09-11.md).
