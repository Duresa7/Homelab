# Galaxy Network Configuration

**Created:** 2026-07-09  
**Last updated:** 2026-11-09

This file is the reference for Galaxy's Proxmox bridge, VLAN interfaces, host routes and cluster-facing addresses. UniFi owns the matching switch-port, VLAN, zone and gateway rules; cross-system changes link both owners.

The cluster as a whole is described in [Cluster Architecture](../Documentation/Architecture/Cluster%20Architecture.md).

## Current Cluster-Facing VLAN Interfaces

| Node | MGMT-A / `vmbr0.70` | Cluster-Net / `vmbr0.71` | Default gateway | VLAN 71 bridge admission |
|---|---|---|---|---|
| `grey-server` | `192.168.70.10/24` | `192.168.71.10/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `purple-server` | `192.168.70.11/24` | `192.168.71.11/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `blue-server` | `192.168.70.12/24` | `192.168.71.12/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `red-server` | `192.168.70.13/24` | `192.168.71.13/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |
| `green-server` | `192.168.70.14/24` | `192.168.71.14/24` | `192.168.70.1` on `vmbr0.70` | `bridge-vids 2-4094` |

`vmbr0.71` is an IP-only host interface with no gateway. It carries Corosync `link1`; the default route remains on `vmbr0.70`. [Galaxy Cluster-Net Corosync Link Addition - 2026-07-10](../Documentation/Change%20Records/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md) records the commands, screenshots and four-node tests. `green-server` carries Corosync `link1` on `192.168.71.14` (live `corosync.conf`, 2026-09-24).

All five nodes admit VLAN IDs 2 through 4094 on the VLAN-aware bridge; step S-09 of the link-addition record replaced `red-server`'s enumerated list with that range. I read `green-server`'s `bridge-vids 2-4094` from its live file on 2026-10-15.

## nic0 Offloads on the M920q Nodes

Since 2026-10-15, the `nic0` stanza on `purple-server`, `green-server` and `red-server` carries a `post-up` line that turns TSO, GSO and GRO off at every boot. `blue-server` has carried it since 2026-11-09:

```text
iface nic0 inet manual
	post-up /sbin/ethtool -K nic0 tso off gso off gro off
```

It is the community workaround for the I219-LM transmit hang in the [Purple NIC incident](../../../../Security/Incidents/Galaxy/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14.md). `grey-server` doesn't have the line because it uses Realtek NICs. Blue went without it while it ran on an M910q, whose I219-LM (2) driver already forces TSO off. On 2026-11-09 Blue moved into an M920q with the same I219-LM (7) as the others, read TSO, GSO and GRO on, and got the line, applied live ([chassis swap](../../../Hardware/Documentation/Change%20Records/Blue%20Chassis%20Swap%20and%20Green%20Memory%20Upgrade%20-%202026-11-09.md#step-6-nic0-offloads-on-blue)). Keep the line if a node's network configuration is rewritten. [Change record](../Documentation/Change%20Records/nic0%20Offloads%20Disabled%20on%20Purple,%20Green%20and%20Red%20-%202026-10-15.md).

## nic0 Is Pinned by MAC Address

Every node names its onboard NIC `nic0` through `/usr/local/lib/systemd/network/50-pmx-nic0.link`, written by the Proxmox installer, which matches on `MACAddress=`. `vmbr0` uses `bridge-ports nic0`. A node's boot drive moved into another chassis, or a replaced motherboard or NIC, boots with the NIC under its default name and no physical bridge port, so it is unreachable until the link file carries the new MAC address. Every node's switch port must also use the UniFi `Proxmox-Trunk` profile, because the node addresses are on tagged VLANs 70 and 71. Blue hit both on 2026-11-09: [blue-server Unreachable After Chassis Swap](../Documentation/Troubleshooting/blue-server%20Unreachable%20After%20Chassis%20Swap%20-%202026-11-09.md).
