# Kasm Lab Network Simplification

**Created:** 2026-07-23  
**Last updated:** 2026-07-23

## What I did

I cut the Kasm security-lab network from seven VLANs to three & replaced its 53 firewall policies with 9. No client had ever attached to those VLANs, so I collapsed the design before rebuilding Kasm itself from scratch. The earlier build carried VLANs 73 through 79, seven custom zones, 53 `KASM` policies, a Proton egress route across four VLANs, & two Proxmox-API rules.

I kept three segments:

| VLAN | Zone | Role | Internet |
|---|---|---|---|
| 74 | KASM-BROWSER | Kasm agent, browser containers, & attacker tools | Proton, kill switch on |
| 77 | MALWARE-OFFLINE | targets & malware detonation | none |
| 79 | EVIDENCE-QUARANTINE | evidence review | none |

I deleted VLANs 73 (CYBER-OPS), 75 (LAB-ATTACK), 76 (LAB-TARGET), & 78 (MALWARE-ONLINE) along with their four zones.

## Firewall changes

I deleted 44 of the 53 `KASM` policies & kept 9. The nine that remain are, per surviving zone, a DHCP allow to the Gateway & a block for other Gateway services, an NTP allow for VLAN 74, & an External block on VLANs 77 & 79. Custom zones already default to Block All, so the deleted per-pair block rules were adding order risk without changing the zone default.

I removed the two Proxmox-API rules (`KASM Allow Core to Grey Proxmox` & `KASM Allow Grey Proxmox to Core`) & the disabled duplicate `KASM Allow Core to Proxmox API`. The Kasm control-plane, attacker-to-target, & evidence-SFTP allows are gone; I'll re-add those against real host IPs when the rebuild defines them. I retargeted the `KASM Lab Proton Egress` route from four VLANs to VLAN 74 only, kill switch still on.

## Verification

After the change the controller returned 26 networks (from 30), 15 firewall zones (from 19), & 9 `KASM` policies (from 53). The three surviving lab networks are enabled; the four deleted VLANs & their zones no longer appear in `unifi_list_networks` or `unifi_list_firewall_zones`. I confirmed each VLAN deletion against its named removal dialog so no active network was touched.

## Tooling note

The UniFi MCP deleted & rebuilt the firewall policies, retargeted the Proton route, & disabled the four VLANs, but it exposes no tool to delete a VLAN or a zone. I removed the four VLANs & four zones through the authenticated UniFi web console.

## Scope boundary

This record covers the network side. I also removed the Proxmox & Kasm build artifacts from the repository, including the `Platforms/Kasm Workspaces/` tree & the Galaxy Kasm preflight record, and then tore down every agent-built Proxmox object, recorded in the [Kasm lab Proxmox teardown](../../../../Compute/Galaxy/Documentation/Change%20Records/Kasm%20Lab%20Proxmox%20Teardown%20-%202026-07-23.md): the ten Kasm VMs & their disks, the KASM-AUTOSCALE pool, the provider user, token, & role, the KASMLAB SDN zone & vnets, the kasm-snippets storage, & the host-firewall line. The cluster stayed quorate at four of four. A full pre-change snapshot of the repository & the live UniFi & Proxmox state sits outside the repository at `D:\Documents\Kasm-Cleanup-Backup-2026-07-23\`.
