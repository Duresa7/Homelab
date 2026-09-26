# Galaxy Network Configuration

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

This file is the reference for Galaxy's Proxmox bridge, VLAN interfaces, host routes and cluster-facing addresses. UniFi owns the matching switch-port, VLAN, zone and gateway rules; cross-system changes link both owners.

The cluster as a whole is described in [Cluster Architecture](../Documentation/Architecture/Cluster%20Architecture.md).

## Current Cluster-Facing VLAN Interfaces

| Node | MGMT-A / `vmbr0.70` | Cluster-Net / `vmbr0.71` | Default gateway | VLAN 71 bridge admission |
|---|---|---|---|---|
| `grey-server` | `192.168.70.10/24` | `192.168.71.10/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `purple-server` | `192.168.70.11/24` | `192.168.71.11/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `blue-server` | `192.168.70.12/24` | `192.168.71.12/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `red-server` | `192.168.70.13/24` | `192.168.71.13/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `green-server` | `192.168.70.14/24` | `192.168.71.14/24` | `192.168.70.1` on `vmbr0.70` | Not recorded |

`vmbr0.71` is an IP-only host interface with no gateway. It carries Corosync `link1`; the default route remains on `vmbr0.70`. [Galaxy Cluster-Net Corosync Link Addition - 2026-07-10](../Documentation/Change%20Records/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md) records the commands, screenshots and four-node tests. `green-server` carries Corosync `link1` on `192.168.71.14` (live `corosync.conf`, 2026-09-24).

The four original nodes admit VLAN IDs 2 through 4094 on the VLAN-aware bridge; step S-09 of the link-addition record replaced `red-server`'s enumerated list with that range. I have not recorded `green-server`'s `bridge-vids` line.
