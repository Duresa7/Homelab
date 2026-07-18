# Infrastructure

**Created:** 2026-07-09  
**Last updated:** 2026-07-09

Infrastructure contains the systems that provide networking, compute, cluster, and physical foundations.

- `Network/` contains Cloudflare and UniFi configuration.
- `Compute/Galaxy/` contains Proxmox cluster architecture, change records, and configuration.
- `Hardware/` contains physical node and device specifications.

Route configuration by enforcement point. Proxmox bridges, Corosync, storage, and Datacenter firewall configuration belong to Galaxy. UniFi VLANs, zones, gateway firewall policies, VPNs, and port profiles belong to UniFi.

