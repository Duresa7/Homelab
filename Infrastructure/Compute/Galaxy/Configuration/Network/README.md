# Galaxy Network Configuration

**Created:** 2026-07-09  
**Last updated:** 2026-07-17

Store Proxmox-owned bridge, bond, VLAN-interface, host-routing, and cluster-facing network configuration here. Keep architecture and change narratives under `Documentation/`, and link to UniFi-owned VLAN or gateway configuration under `Infrastructure/Network/UniFi/` when a change spans both systems.

The broad current architecture remains documented in the [Galaxy cluster setup document](../../Documentation/Architecture/Galaxy%20Cluster%20Setup%20Document.md).

## Current Cluster-Facing VLAN Interfaces

| Node | MGMT-A / `vmbr0.70` | Cluster-Net / `vmbr0.71` | Default gateway | VLAN 71 bridge admission |
|---|---|---|---|---|
| `grey-server` | `192.168.70.10/24` | `192.168.71.10/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `purple-server` | `192.168.70.11/24` | `192.168.71.11/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `blue-server` | `192.168.70.12/24` | `192.168.71.12/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `red-server` | `192.168.70.13/24` | `192.168.71.13/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |

`vmbr0.71` is an IP-only Proxmox host interface with no gateway. It is dedicated to the redundant Corosync link and leaves the original management route unchanged. The implementation, per-node configuration exports, rollback copies, screenshots, and exact verification commands are recorded in [Galaxy Cluster-Net Corosync Link Addition - 2026-07-10](../../Documentation/Change%20Records/Galaxy%20Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md).

All four nodes now use the broad `2-4094` VLAN-aware bridge range. S-09 normalized red-server from its earlier enumerated list without changing either host IP, the default route, or the Corosync configuration.
