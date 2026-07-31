# Galaxy Proxmox Cluster

**Created:** 2026-07-09  
**Last updated:** 2026-07-31

Galaxy is my five-node Proxmox VE 9.2.5 cluster. This directory owns its bridge configuration, two-link Corosync setup, storage references, Datacenter firewall, change records, & troubleshooting history.

## Records

- [Cluster architecture and setup](Documentation/Architecture/Galaxy%20Cluster%20Setup%20Document.md)
- [Change records](Documentation/Change%20Records/)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Galaxy TODO](Documentation/TODO.md)
- [Five-node rolling replacement plan](Documentation/Change%20Plans/Galaxy%20Cluster%20Node%20Rename%20Rolling%20Replacement%20Plan%20-%202026-07-31.md)
- [Green baseline and monitoring change](Documentation/Change%20Records/Galaxy%20Green%20Baseline%20and%20Monitoring%20-%202026-07-31.md)
- [Proxmox Datacenter firewall](Configuration/Firewall/Galaxy%20Data%20Center%20Firewall.md)
- [Current inventory](../../../Operations/Inventory/Galaxy/Galaxy%20Inventory.md)
- [Hardware inventory](../../Hardware/Nodes.md)

UniFi owns the matching VLAN, zone, switch-port, & gateway policy records under `Infrastructure/Network/UniFi/`. Galaxy change records link those files instead of copying them.
