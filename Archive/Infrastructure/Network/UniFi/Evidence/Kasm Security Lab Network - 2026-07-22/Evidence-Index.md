# Kasm Security Lab Network Evidence Index

**Created:** 2026-07-22  
**Last updated:** 2026-08-04

## Scope

I retained these screenshots while building the UniFi boundary for the Kasm security lab. They show the reviewed or applied graphical state without passwords, tokens, network object IDs, or a visible cursor. Controller API verification supplied the exact counts and assignments recorded in the [Kasm deployment record](../../../../../Platforms/Kasm%20Workspaces/Documentation/Deployment.md). The two route captures stay local because their routing table also displays the upstream public address.

## Captures

| File | State shown |
| --- | --- |
| [Firewall zones](Screenshots/unifi-firewall-zones-2026-07-22.png) | Custom-zone table after creation |
| [Lab zone entries](Screenshots/unifi-firewall-zones-lab-entries-2026-07-22.png) | All seven Kasm lab zones in one table view |
| [Kasm policies](Screenshots/unifi-kasm-firewall-policies-2026-07-22.png) | Filtered Kasm firewall policies and DHCP rule detail |
| `Screenshots/unifi-kasm-proton-route-preview-2026-07-22.png` | Local-only capture of four target VLANs and the enabled kill switch before creation |
| `Screenshots/unifi-kasm-proton-route-active-2026-07-22.png` | Local-only capture of the enabled route through ProtonVPN with four target VLANs and the kill switch |
| [Trunk preview](Screenshots/unifi-proxmox-trunk-kasm-vlans-preview-2026-07-22.png) | Proxmox trunk edit with the expanded tagged-VLAN selection |
| [Applied trunk](Screenshots/unifi-proxmox-trunk-kasm-vlans-active-2026-07-22.png) | Applied `Proxmox-Trunk` profile showing `Edit (16)` tagged VLANs |

## Limits

These captures prove controller configuration, not packet flow. One harmless client on each VLAN still must prove DHCP, DNS, allowed workflows, blocked destinations, Proton egress, and fail-closed behavior before I create a malware-capable template.
