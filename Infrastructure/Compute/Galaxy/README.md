# Galaxy Proxmox Cluster

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

Galaxy is my four-node Proxmox VE 9.2.2 cluster. This directory owns its bridge configuration, two-link Corosync setup, storage references, Datacenter firewall, change records, & troubleshooting history.

## Records

- [Cluster architecture and setup](Documentation/Architecture/Galaxy%20Cluster%20Setup%20Document.md)
- [Change records](Documentation/Change%20Records/)
- [Troubleshooting log](Documentation/Troubleshooting-Log.md)
- [Galaxy TODO](Documentation/TODO.md)
- [Proxmox Datacenter firewall](Configuration/Firewall/Galaxy%20Data%20Center%20Firewall.md)
- [Current inventory](../../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md)
- [Hardware inventory](../../Hardware/Nodes.md)

UniFi owns the matching VLAN, zone, switch-port, & gateway policy records under `Infrastructure/Network/UniFi/`. Galaxy change records link those files instead of copying them.
