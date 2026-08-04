# Galaxy Proxmox Cluster

**Created:** 2026-07-09  
**Last updated:** 2026-08-04

Galaxy is my five-node Proxmox VE 9.2.5 cluster. This directory owns its bridge configuration, two-link Corosync setup, storage references, Datacenter firewall, change records, & troubleshooting history.

## Records

- [Cluster architecture and setup](Documentation/Architecture/Galaxy%20Cluster%20Setup%20Document.md)
- [Cluster-facing network configuration](Configuration/network.md)
- [Corosync configuration reference](Configuration/Corosync/README.md)
- [Change records](Documentation/Change%20Records/)
- [Original node preparation and pre-join remediation](Documentation/Change%20Records/Galaxy%20Cluster%20Expansion%20Node%20Preparation%20-%202026-05-27.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Galaxy TODO](Documentation/TODO.md)
- [Green baseline and monitoring change](Documentation/Change%20Records/Galaxy%20Green%20Baseline%20and%20Monitoring%20-%202026-07-31.md)
- [Proxmox Datacenter firewall](Configuration/Datacenter-Firewall.md)
- [Current inventory](../../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md)
- [Hardware inventory](../../Hardware/Nodes.md)

UniFi owns the matching VLAN, zone, switch-port, & gateway policy records under `Infrastructure/Network/UniFi/`. Galaxy change records link those files instead of copying them.
