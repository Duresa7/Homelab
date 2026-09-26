# Infrastructure

**Created:** 2026-07-09  
**Last updated:** 2026-09-06

Infrastructure records the two network owners, the five-node Galaxy cluster, and the physical hardware beneath them.

- `Network/` holds my Cloudflare and UniFi configuration.
- `Compute/Galaxy/` holds the Proxmox cluster architecture, change records, and configuration.
- [`Hardware/`](Hardware/README.md) holds physical node, workstation, and power-equipment specifications.

Configuration follows its enforcement point. Proxmox bridges, Corosync, storage, and the Datacenter firewall belong to Galaxy. UniFi owns VLANs, zones, gateway policies, VPNs, and port profiles.
