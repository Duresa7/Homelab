# S01 Preflight

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

- I confirmed MGMT-A is VLAN 70 and contains the four Proxmox management addresses.
- I confirmed the approved-device UniFi policy contains Jedi PC, Pixel, MacBook Air, and `ansible-01`.
- I confirmed the existing WireGuard Vpn-to-MGMT policy is enabled and broad.
- I confirmed the Galaxy firewall has matching device, service, monitoring, cluster, and WireGuard entries.
- I saved the pre-change UniFi snapshot as `firewall_20260727T122034Z_before.json`, retained on my workstation outside this repository.
- I downloaded the live Proxmox firewall to `Exports/cluster.fw.before-2026-07-27`.
