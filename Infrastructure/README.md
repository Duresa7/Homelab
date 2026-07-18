# Infrastructure

**Created:** 2026-07-09  
**Last updated:** 2026-07-18

This is where I keep the systems that provide my networking, compute, cluster, and physical foundations.

- `Network/` holds my Cloudflare and UniFi configuration.
- `Compute/Galaxy/` holds the Proxmox cluster architecture, change records, and configuration.
- `Hardware/` holds physical node and device specifications.

I route configuration by enforcement point. Proxmox bridges, Corosync, storage, and Datacenter firewall configuration belong to Galaxy. UniFi VLANs, zones, gateway firewall policies, VPNs, and port profiles belong to UniFi.
