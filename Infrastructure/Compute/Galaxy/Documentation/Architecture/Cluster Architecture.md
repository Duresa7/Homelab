# Galaxy Cluster Architecture

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

Galaxy is my five-node Proxmox VE 9.2.11 cluster. Every node keeps its guests on its own disks: there is no shared storage and no guest is under HA. I checked everything on this page against the cluster on 2026-09-24.

![Galaxy cluster: five Proxmox nodes on MGMT-A and Cluster-Net, with per-node storage and guests](../../../../../Assets/Diagrams/galaxy-cluster.svg)

## Nodes

| Node | MGMT-A (link0) | Cluster-Net (link1) | CPU | Memory | Guests on 2026-09-24 |
| --- | --- | --- | --- | --- | --- |
| grey-server | 192.168.70.10 | 192.168.71.10 | Ryzen 7 3700X, 8 cores / 16 threads, GTX 1080 Ti | 62.72 GiB | VMs 102, 103, 105, 109, 200, 301, 302, 303 and 310, CT 110, and templates 101, 300 and 9000 |
| purple-server | 192.168.70.11 | 192.168.71.11 | i5-8500T, 6 cores | 15.46 GiB | VMs 116 `app-01`, 121 `edge-01`, 401 `alpha-prod-01` |
| blue-server | 192.168.70.12 | 192.168.71.12 | i5-7500T, 4 cores | 5.68 GiB | CTs 100 `ansible-01`, 104 `monitor-01`, 107 `docker-network`, 108 `docker-blue` |
| red-server | 192.168.70.13 | 192.168.71.13 | i5-8500T, 6 cores | 15.46 GiB | CT 842 `media-01` |
| green-server | 192.168.70.14 | 192.168.71.14 | i5-8500T, 6 cores | 15.46 GiB | None; unresolved host memory errors since 2026-09-20 |

Grey carries most of the load: 51.61 of its 62.72 GiB was in use on 2026-09-24. The full hardware record is [Nodes](../../../../Hardware/Nodes.md) and the guest records are in [Operations/Inventory/Galaxy](../../../../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md).

## Corosync and quorum

Corosync runs `knet` in passive link mode with two links and no explicit priorities, so it prefers `link0`:

- `link0` on MGMT-A, VLAN 70, `192.168.70.0/24`, through each node's `vmbr0.70`, which also holds the default route.
- `link1` on Cluster-Net, VLAN 71, `192.168.71.0/24`, through `vmbr0.71`, an IP-only interface with no gateway and no DHCP.

On 2026-09-24 `/etc/pve/corosync.conf` was at `config_version: 9` with five nodes, and `pvecm status` reported five expected and five total votes, quorate. The versioned copy in [Configuration/Corosync](../../Configuration/Corosync/README.md) is still the four-node version 8 file. The bridge and VLAN interfaces are in [network.md](../../Configuration/network.md).

## Storage

Each node's storage belongs to that node alone.

| Node | Storage | Type | Backing device | Holds |
| --- | --- | --- | --- | --- |
| grey-server | `local-lvm` | LVM-thin | 1 TB Crucial P310 NVMe | VMs 102, 103, 105 and CT 110's rootfs |
| grey-server | `ssd-lvm1` | LVM-thin | 2 TB Crucial BX500 SATA SSD | VMs 109, 200, 301, 302, 303, 310 and the three templates |
| grey-server | `hddpool-1` | ZFS | 2 TB Toshiba HDD | CT 110's `/data` (Immich) |
| purple-server | `local-lvm` | LVM-thin | 256 GB Toshiba NVMe | VMs 116, 121, 401 |
| purple-server | `ssd-lvm2` | LVM-thin, restricted to Purple | Samsung 850 EVO 250 GB | Empty |
| blue-server | `local-lvm` | LVM-thin | 256 GB Samsung NVMe | CTs 100, 104, 107, 108 |
| red-server | `local-lvm` | LVM-thin | 256 GB Samsung NVMe | CT 842's rootfs |
| red-server | host ext4 bind mount | Directory | 1 TB Seagate HDD | CT 842's `/data` media library |
| green-server | `local-lvm` | LVM-thin | 256 GB Samsung NVMe | Empty |

Every node also has a `local` directory storage for ISOs and templates. Usage figures are in [Nodes](../../../../Hardware/Nodes.md#cluster-storage). Moving a guest to another node copies its disks across the network; the September moves are in the [change records](../Change%20Records/). The [shared storage research](../Shared%20Storage%20Migration%20and%20Load%20Balancing%20Research%20-%202026-08-23.md) of 2026-08-23 covers what shared storage would take; nothing from it has been built.

## High availability

`ha-manager config` and `ha-manager rules config` are empty. No guest is an HA resource, so a node failure stops its guests until the node returns. CT 107 and CT 108 were the last HA resources; their removal is recorded in [CT 107 and CT 108 HA Removal](../Change%20Records/CT%20107%20and%20CT%20108%20HA%20Removal%20-%202026-09-24.md). The HA services stay idle on every node, with the CRM master on `green-server`.

## Guest networking

`vmbr0` on each node is a VLAN-aware bridge. Guests attach to it with a VLAN tag, and the UniFi switch port carries the tagged VLANs through the `Proxmox-Trunk` profile. The VLAN and zone of every network are in [UniFi Networks and VLANs](../../../../Network/UniFi/Configuration/network-vlan.md).

## Firewall model

Two firewalls sit in front of a node, and a path needs both:

1. The UniFi zone firewall decides whether traffic reaches MGMT-A at all. [UniFi Firewall Policies](../../../../Network/UniFi/Configuration/firewall.md).
2. The Proxmox Datacenter firewall enforces `pve_mgmt` on every node's `PVEFW-HOST-IN` chain, admitting named IP sets on TCP 22, 8006 and 3128 and dropping the rest. [Galaxy Datacenter Firewall](../../Configuration/Datacenter-Firewall.md).

Guest firewalls are set per NIC in each guest's configuration.

## Provisioning and monitoring

A new node installs over UEFI PXE on Server-Provision, VLAN 5, from [Galaxy PXE](../../../../../Platforms/Galaxy%20PXE/README.md) on `ansible-01`, then joins over SSH and moves to MGMT-A and Cluster-Net. Every node runs node_exporter on TCP 9100 and a Wazuh agent. `monitor-01` reads the Proxmox API through the PVE exporter, and `grey-server` serves UPS-02 over NUT on TCP 3493.

## Records

- [Change records](../Change%20Records/), including the [three-node formation](../Change%20Records/Three-Node%20Cluster%20Formation%20-%202026-05-30.md) of 2026-05-30 and the [Cluster-Net link addition](../Change%20Records/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10.md) of 2026-07-10
- [Troubleshooting index](../Troubleshooting/README.md)
- [Galaxy TODO](../TODO.md)
