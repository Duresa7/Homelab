# Galaxy Proxmox Cluster

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

Galaxy is my five-node Proxmox VE 9.2.11 cluster. It runs 12 VMs, six LXCs and three templates on node-local storage, with no shared storage and no HA resources. This folder owns the bridges, the two-link Corosync setup, the storage references, the Datacenter firewall, and the cluster's change and troubleshooting records.

![Galaxy cluster: five Proxmox nodes on MGMT-A and Cluster-Net, with per-node storage and guests](../../../Assets/Diagrams/galaxy-cluster.svg)

| Fact | Value (2026-09-24) |
| --- | --- |
| Nodes | `grey-server`, `purple-server`, `blue-server`, `red-server`, `green-server` (192.168.70.10 to .14) |
| Quorum | 5 of 5 votes, `config_version: 9` |
| Corosync | `link0` on MGMT-A (VLAN 70), `link1` on Cluster-Net (VLAN 71, 192.168.71.0/24) |
| Guests | 18 (16 running; `kali-pen` and `HQ-WS001` stopped); `green-server` holds none |
| HA | `ha-manager config` empty |
| Open fault | Host memory errors on `green-server` since 2026-09-20 |

## Current state

- [Cluster architecture](Documentation/Architecture/Cluster%20Architecture.md)
- [Galaxy inventory](../../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md): [VMs](../../../Operations/Inventory/Galaxy/VMs.md), [LXCs](../../../Operations/Inventory/Galaxy/LXCs.md), [Services](../../../Operations/Inventory/Galaxy/Services.md)
- [Node hardware](../../Hardware/Nodes.md)
- [Bridge and VLAN configuration](Configuration/network.md)
- [Corosync configuration](Configuration/Corosync/README.md)
- [Storage configuration](Configuration/Storage/README.md)
- [Datacenter firewall](Configuration/Datacenter-Firewall.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Galaxy TODO](Documentation/TODO.md)

UniFi owns the VLAN, zone, switch-port and gateway policy records under [Infrastructure/Network/UniFi](../../Network/UniFi/README.md).

## Change records since 2026-09-01

| Date | Record |
| --- | --- |
| 2026-09-24 | [CT 107 and CT 108 HA Removal](Documentation/Change%20Records/CT%20107%20and%20CT%20108%20HA%20Removal%20-%202026-09-24.md) |
| 2026-09-24 | [HQ-WS001 Memory at 8 GiB](Documentation/Change%20Records/HQ-WS001%20Memory%20at%208%20GiB%20-%202026-09-24.md) |
| 2026-09-24 | [monitor-01 Rootfs at 20 GiB](Documentation/Change%20Records/monitor-01%20Rootfs%20at%2020%20GiB%20-%202026-09-24.md) |
| 2026-09-24 | [ubuntu-dev 12 GiB Applied](Documentation/Change%20Records/ubuntu-dev%2012%20GiB%20Applied%20-%202026-09-24.md) |
| 2026-09-23 | [win11-dev Grey Migration](Documentation/Change%20Records/win11-dev%20Grey%20Migration%20-%202026-09-23.md) |
| 2026-09-21 | [win11-dev Completion](Documentation/Change%20Records/win11-dev%20Completion%20-%202026-09-21.md) |
| 2026-09-20 | [win11-dev Provisioning and Green Memory Failure](Documentation/Change%20Records/win11-dev%20Provisioning%20and%20Green%20Memory%20Failure%20-%202026-09-20.md) |
| 2026-09-12 | [alpha-prod-01 Purple Migration](Documentation/Change%20Records/alpha-prod-01%20Purple%20Migration%20-%202026-09-12.md) |
| 2026-09-12 | [ansible-01 Blue Migration](Documentation/Change%20Records/ansible-01%20Blue%20Migration%20-%202026-09-12.md) |
| 2026-09-11 | [app-01 and edge-01 Purple Migration](Documentation/Change%20Records/app-01%20and%20edge-01%20Purple%20Migration%20-%202026-09-11.md) |
| 2026-09-11 | [app-01 64 GiB Boot Disk Replacement](Documentation/Change%20Records/app-01%2064%20GiB%20Boot%20Disk%20Replacement%20-%202026-09-11.md) |
| 2026-09-11 | [app-01 Disk Sizing Assessment](Documentation/Change%20Records/app-01%20Disk%20Sizing%20Assessment%20-%202026-09-11.md) |
| 2026-09-10 | [app-01 and edge-01 Purple Migration Assessment](Documentation/Change%20Records/app-01%20and%20edge-01%20Purple%20Migration%20Assessment%20-%202026-09-10.md) |
| 2026-09-10 | [ubuntu-dev Memory Assessment](Documentation/Change%20Records/ubuntu-dev%20Memory%20Assessment%20-%202026-09-10.md) |
| 2026-09-08 | [ubuntu-dev NVMe Storage Move](Documentation/Change%20Records/ubuntu-dev%20NVMe%20Storage%20Move%20-%202026-09-08.md) |
| 2026-09-07 | [PermitRootLogin Aligned on purple-server and blue-server](Documentation/Change%20Records/PermitRootLogin%20Aligned%20on%20purple-server%20and%20blue-server%20-%202026-09-07.md) |
| 2026-09-06 | [CT 110 Phantom Unused Volume Removed](Documentation/Change%20Records/CT%20110%20Phantom%20Unused%20Volume%20Removed%20-%202026-09-06.md) |
| 2026-09-06 | [docker-blue Firewall Grant Narrowed to pve_ssh_manager](Documentation/Change%20Records/docker-blue%20Firewall%20Grant%20Narrowed%20to%20pve_ssh_manager%20-%202026-09-06.md) |
| 2026-09-04 | [PVE 9.2.11 Package Update](Documentation/Change%20Records/PVE%209.2.11%20Package%20Update%20-%202026-09-04.md) |

Earlier records, from the [three-node formation](Documentation/Change%20Records/Three-Node%20Cluster%20Formation%20-%202026-05-30.md) of 2026-05-30 onward, are in [Change Records](Documentation/Change%20Records/). The [shared storage and load balancing research](Documentation/Shared%20Storage%20Migration%20and%20Load%20Balancing%20Research%20-%202026-08-23.md) of 2026-08-23 covers what shared storage would take.
