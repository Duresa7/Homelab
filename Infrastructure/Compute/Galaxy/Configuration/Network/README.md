# Galaxy Network Configuration

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

This directory owns the Proxmox bridge, VLAN interface, host route, & cluster-facing network references. UniFi owns the matching switch-port, VLAN, zone, & gateway rules; cross-system changes link both owners.

The broad current architecture is documented in the [Galaxy cluster setup document](../../Documentation/Architecture/Galaxy%20Cluster%20Setup%20Document.md).

## Current Cluster-Facing VLAN Interfaces

| Node | MGMT-A / `vmbr0.70` | Cluster-Net / `vmbr0.71` | Default gateway | VLAN 71 bridge admission |
|---|---|---|---|---|
| `grey-server` | `192.168.70.10/24` | `192.168.71.10/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `purple-server` | `192.168.70.11/24` | `192.168.71.11/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `blue-server` | `192.168.70.12/24` | `192.168.71.12/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `red-server` | `192.168.70.13/24` | `192.168.71.13/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |

`vmbr0.71` is an IP-only host interface with no gateway. It carries Corosync `link1`; the default route remains on `vmbr0.70`. [Galaxy Cluster-Net Corosync Link Addition - 2026-07-10](../../Documentation/Change%20Records/Galaxy%20Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md) records the commands, screenshots, & four-node tests.

All four nodes admit VLAN IDs 2 through 4094 on the VLAN-aware bridge. Step S-09 replaced `red-server`'s enumerated list with that range without changing either host IP, the default route, or Corosync.
