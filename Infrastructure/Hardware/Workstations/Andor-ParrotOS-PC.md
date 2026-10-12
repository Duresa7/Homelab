# Andor-ParrotOS-PC

**Created:** 2026-10-11  
**Last updated:** 2026-10-12

Andor-ParrotOS-PC is my Parrot Security desktop for security work, on Secure, VLAN 50. It has the same admin access as Jedi PC. It runs on the same physical hardware as [ObiPC](ObiPC.md): an 8-core Ryzen 7 7700X, 32 GB of DDR5, an RTX 3070, a 1 TB and a 500 GB NVMe drive, and a 2.5 Gbps Ethernet adapter. On 2026-10-11 I removed ObiPC's Windows 11 install and installed Parrot Security 7.4. This is temporary. I treat Andor-ParrotOS-PC and ObiPC as two separate machines, and ObiPC's records stay as they are. I read everything below from the machine over SSH that evening.

## System Overview

| Property | Value |
|---|---|
| Name | Andor-ParrotOS-PC; Linux hostname `parrot`; the UniFi client alias is the same name, and the DHCP hostname still reads `Obipc` |
| User | `dkadi`, in `sudo` with a password |
| Role | Security work and administration, on par with Jedi PC |
| Network | Secure, VLAN 50, DHCP, `192.168.50.102` |
| Manufacturer | ASUS |
| Model | System Product Name (custom build), desktop chassis |

## Operating System

| Property | Value |
|---|---|
| OS | Parrot Security 7.4 (echo) |
| Kernel | `7.1.13+parrot7-amd64` since the 10:49 PM reboot; `7.0.9+parrot7-amd64` remains installed |
| Installed | 2026-10-11, 8:10 PM Eastern (root filesystem creation time) |
| Firmware | UEFI; the only firmware boot entry for an internal disk is `Parrot` |

No Windows Boot Manager entry remains, and the 500 GB drive holds only a data partition with no EFI system partition. While Parrot is installed, the hardware cannot boot ObiPC's Windows.

When ObiPC's Windows goes back on this hardware, Andor-ParrotOS-PC's MAC-based UniFi grants go with the network adapter. I remove them first, following [Before ObiPC's Windows returns](../../Network/UniFi/Documentation/Change%20Records/Andor-ParrotOS-PC%20Admin%20Access%20-%202026-10-11.md#before-obipcs-windows-returns).

## Processor (CPU)

| Property | Value |
|---|---|
| Model | AMD Ryzen 7 7700X 8-Core Processor |
| Cores | 8 |
| Logical Processors | 16 |
| Max Clock Speed | 5535 MHz boost, as Linux reports it |

## Memory (RAM)

**Total Installed:** 32 GB (30 GiB usable)

| Slot | Manufacturer | Part Number | Capacity | Configured Speed |
|---|---|---|---|---|
| DIMM 1, first bank | G.Skill | F5-6000J3636F16G | 16 GB | 6000 MT/s |
| DIMM 1, second bank | G.Skill | F5-6000J3636F16G | 16 GB | 6000 MT/s |

Both DIMM 0 slots are empty. Under Windows on 2026-09-11 the kit ran at 4800. It now reports its rated 6000 MT/s, so the memory profile has been enabled in the BIOS since then.

## Graphics (GPU)

| Adapter | Model |
|---|---|
| Discrete | NVIDIA GeForce RTX 3070 (GA104, Lite Hash Rate), 8 GB, VBIOS 94.04.46.00.F2 |
| Integrated | AMD Radeon Graphics (Raphael, in the 7700X) |

The RTX 3070 runs NVIDIA driver 615.71.09 with the open kernel modules, from NVIDIA's Debian 13 repository, which apt prefers for the driver packages through a pin. Before that it was on `nouveau`. [NVIDIA Driver Installation](../Documentation/Change%20Records/Andor-ParrotOS-PC%20NVIDIA%20Driver%20Installation%20-%202026-10-11.md).

## Motherboard and BIOS

| Property | Value |
|---|---|
| Board | ASUS TUF GAMING B650-PLUS WIFI |
| BIOS | American Megatrends 3201, 2025-01-11 |

## Storage

| Disk | Capacity | Bus | Layout | Use |
|---|---|---|---|---|
| Samsung SSD 980 1TB | 931.5 GiB | NVMe | 300 MiB EFI, 931.2 GiB Btrfs | Parrot: `/`, `/home` and swap |
| Crucial P310 500GB (`CT500P310SSD8`) | 465.8 GiB | NVMe | 16 MiB reserved, 465.7 GiB NTFS | The old Windows `D:` `Storage` volume, not mounted |

Two USB drives (a Samsung Type-C 1100 and a SanDisk 3.2Gen1, both exFAT) were attached when I read the disks. They are removable media, not part of the build.

## Network

| Adapter | Device | Link | State |
|---|---|---|---|
| `eno1` | Realtek RTL8125 2.5GbE | 2.5 Gbps | Up, the only connection |
| `wlp9s0` | Realtek RTL8852BE Wi-Fi 6 | none | Down |

## Management and access

- **SSH Manager:** server `andor_parrot_os_pc`, key login as `dkadi` with password-backed sudo: [Andor-ParrotOS-PC SSH Manager Enrollment](../../../Platforms/Docker%20MCP%20Gateway/Documentation/Change%20Records/Andor-ParrotOS-PC%20SSH%20Manager%20Enrollment%20-%202026-10-11.md).
- **Its own key:** ED25519 `andor-parrotos-pc`, `SHA256:EkErC2I8oBnZLf7PK2339LfRK9jCrbUXzAL49c8ZMRA`, managed as identity `andor-parrotos-pc` on the same 16 hosts as Jedi PC. Like Jedi PC's key, it is also in `ai-agent`'s `authorized_keys` on `ubuntu-dev`, which I set up by hand. The UniFi and Proxmox grants that match Jedi PC's are in [Andor-ParrotOS-PC Admin Access](../../Network/UniFi/Documentation/Change%20Records/Andor-ParrotOS-PC%20Admin%20Access%20-%202026-10-11.md).
- **SSH:** key-only since 2026-10-12. Root login is off, and `dkadi` accepts `mac-air3-dkadi`, `jedi-pc`, `parrot-os-mac` and `ai-agent@ubuntu-dev` (the SSH Manager's key): [Andor-ParrotOS-PC SSH Lockdown](../Documentation/Change%20Records/Andor-ParrotOS-PC%20SSH%20Lockdown%20-%202026-10-12.md).
- **Password:** `dkadi` uses the standard account password, at the console and for `sudo`. SSH no longer accepts it.
