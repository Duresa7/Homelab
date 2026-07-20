# Infrastructure

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

Infrastructure records the two network owners, the four-node Galaxy cluster, & the physical hardware beneath them.

- `Network/` holds my Cloudflare and UniFi configuration.
- `Compute/Galaxy/` holds the Proxmox cluster architecture, change records, and configuration.
- `Hardware/` holds physical node and device specifications.

Configuration follows its enforcement point. Proxmox bridges, Corosync, storage, & the Datacenter firewall belong to Galaxy. UniFi owns VLANs, zones, gateway policies, VPNs, & port profiles.
