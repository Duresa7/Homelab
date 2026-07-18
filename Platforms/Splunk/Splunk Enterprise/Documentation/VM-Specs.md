# Splunk SIEM: VM Specifications

**Created:** 2026-07-08  
**Last updated:** 2026-07-18

**VM name:** `splunk-siem`
**VMID:** 109
**Proxmox host:** `grey-server`
**Purpose:** Splunk Enterprise (SIEM / log aggregation), homelab
**Documented:** 2026-06-28

---

## Compute

| Setting | Value | Notes |
|---|---|---|
| Cores | 6 (raised from 4 on 2026-07-02) | Single socket; I bumped it to resolve a CPU-bound Splunk ES install/setup issue; see [Splunk ES troubleshooting log](../../Splunk%20ES/Documentation/Troubleshooting-Log.md) #1 |
| Sockets | 1 | |
| CPU type | `host` | Passes through host CPU features for best performance |
| NUMA | 0 (off) | Single-socket host, not needed |
| Memory | 12288 MiB (12 GiB) | Unchanged; matches Splunk reference spec; 8 GiB floor |

## Firmware / Machine

| Setting | Value | Notes |
|---|---|---|
| BIOS | OVMF (UEFI) | |
| Machine | q35 | Modern PCIe chipset |
| EFI disk | `ssd-lvm1:1`, efitype=4m | UEFI vars store |
| OS type | l26 | Linux 2.6+/6.x kernel |
| QEMU guest agent | Enabled (`agent: 1`) | Install `qemu-guest-agent` in guest |

## Storage

| Setting | Value | Notes |
|---|---|---|
| Disk | `scsi0` → `ssd-lvm1:150` | 150 GiB, single disk (OS + Splunk data) |
| Controller | `virtio-scsi-single` | |
| SSD emulation | `ssd=on` | Guest sees it as SSD; enables TRIM |
| Discard | `discard=on` | TRIM reclaims freed index space |
| IO thread | `iothread=on` | Dedicated I/O thread for the disk |
| Cache | Default (No cache) | Safe for SIEM (no data loss on power cut) |
| Backing storage | SSD-backed LVM (`ssd-lvm1`) | Splunk is I/O-bound, so SSD required |

## Network

| Setting | Value | Notes |
|---|---|---|
| Interface (Proxmox) | `net0` → virtio | |
| Interface (guest) | `ens18` | Red Hat Virtio network device |
| Bridge | `vmbr0` | |
| VLAN tag | **72** (Security-A / REDACTED_PRIVATE_ORG_LABEL-Security) | Dedicated security and monitoring tier |
| Subnet | 192.168.72.0/24 | Static workload range `.2`–`.5`; DHCP pool starts at `.6` |
| MAC address | `REDACTED_MAC_016` | |
| IP address | 192.168.72.3/24 | Static NetworkManager profile |
| Default route | 192.168.72.1 | |
| DNS | 192.168.72.1 | |
| Firewall | Enabled (`firewall=1`) | Proxmox firewall on |

## Install media

| Setting | Value |
|---|---|
| ISO | `Rocky-10.2-x86_64-boot.iso` (mounted on `ide2`, cdrom) |
| OS | Rocky Linux 10.2 (x86_64) |
| Install type | Minimal / Server, no desktop environment |
