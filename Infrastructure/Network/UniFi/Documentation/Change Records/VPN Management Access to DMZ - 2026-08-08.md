# VPN Management Access to DMZ

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

**Implementation date:** 2026-08-08  
**Status:** Complete. The VPN-to-DMZ policy is live; the two `debian-dev` entries were replaced on 2026-08-13 and the guest was destroyed on 2026-08-14.  
**Affected systems:** policies `Device Access --> Proxmox`, `Allow VPN Management Access to DMZ`, `Allow Monitor to Personal-A monitoring`

On 2026-08-08 I made three UniFi changes when `debian-dev` (`192.168.40.135`) became my development workstation. I wrote this record on 2026-09-25 from the paragraphs the firewall view carried; no export was retained.

## What changed

1. **Proxmox access for `debian-dev`.** I added its MAC to `Device Access --> Proxmox`, taking the policy from four client MACs to five. The Proxmox side needed `192.168.40.135` in `pve_admins` as well; see the [Galaxy Datacenter firewall](../../../../Compute/Galaxy/Configuration/Datacenter-Firewall.md).
2. **VPN to DMZ.** I added `Allow VPN Management Access to DMZ`, so the Management Access VPN reaches `edge-01` from outside the network. Before the policy existed the controller returned no user rule for the VPN-to-DMZ zone pair, which is why the DMZ was the one zone the VPN could not reach. The rule names the Management Access network, not the whole `Vpn` zone, so Game-Access still cannot reach the DMZ. It does not weaken `Block DMZ to Internal`, which governs the opposite direction.
3. **Exporter scrape.** I added `192.168.40.135` to the destination list of `Allow Monitor to Personal-A monitoring`, so `monitor-01` could scrape the host's node_exporter. That policy names addresses, not the Internal zone, so a new exporter on Personal-A stays unreachable until its address is listed. Before the edit TCP 9100 from `192.168.73.2` to `192.168.40.135` timed out, while TCP 1514 and 1515 to the Wazuh manager already worked through `Allow Internal to AlphaSec-Security`.

## Superseded

On 2026-08-13 I moved the workstation entries to `ubuntu-dev`. [ubuntu-dev Workstation Access](ubuntu-dev%20Workstation%20Access%20-%202026-08-13.md).
