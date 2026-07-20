# UniFi Network Walkthrough

**Created:** 2026-07-20  
**Last updated:** 2026-07-20

## What This Guide Covers

This guide follows the network work that supports Galaxy & the hosted platforms: VLANs, firewall zones, the Security-A migration, the Access-A egress rules, local DNS, & the switch-port checks needed for Corosync VLAN 71.

## Current Status and Verified Versions

The active records cover VLAN 40 for personal workloads, VLAN 71 for Cluster-Net, VLAN 72 for Security-A, VLAN 80 for servers, VLAN 85 for Access-A, & VLAN 90 for the DMZ. The `docker-network` guest uses `192.168.85.2`; Security-A services use `192.168.72.2` & `192.168.72.3`.

## What You Need

- Administrator access to the UniFi controller.
- A current export or screenshot of the affected VLAN, zone, port, & firewall tables.
- Console access to any Proxmox node whose management or Corosync path will change.
- The exact source, destination, protocol, & port list for each policy.

## How the Pieces Fit Together

> Diagram placeholder

## Walkthrough

### Step 1: Record VLANs and Zones

I start with the current [VLAN inventory](../Infrastructure/Network/UniFi/Configuration/VLANs/network-vlan.md) & [zone inventory](../Infrastructure/Network/UniFi/Configuration/Zones/zone.md). A VLAN ID, subnet, gateway, DHCP state, & zone assignment must agree before I write a policy against it.

### Step 2: Verify Switch Trunks

For Cluster-Net, I checked all four Proxmox switch ports before adding `vmbr0.71`. VLAN 71 was already tagged to grey, purple, & blue; red needed the VLAN admitted before its host interface could communicate.

![UniFi state before the Cluster-Net change](../Infrastructure/Compute/Galaxy/Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Network-Segmentation-Cluster-Net-Prechange-UniFi-Dashboard-2026-07-10.png)

### Step 3: Migrate the Security Services

I moved Wazuh, Prometheus, Grafana, Splunk, HEC, & SC4S from the earlier management addresses into Security-A. I updated the guest addresses, DNS or client targets, & firewall destinations in the same bounded change, then checked every listener from an allowed source.

### Step 4: Add Ordered Access-A Egress

I created three rules for `docker-network` in this order:

1. Allow TCP 80 & 443 from `192.168.85.2`.
2. Allow UDP 123 from `192.168.85.2`.
3. Block the remaining Access-A traffic to External.

![Access-A egress rules after deployment](../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S05A-UniFi-Access-A-Egress-Policies-After-2026-07-11.jpg)

### Step 5: Add Local DNS

I added `<YOUR_NETBIRD_DOMAIN>` as an A record for `192.168.85.2` with TTL 300. The browser path, NPM certificate, & NetBird HTTPS check all depend on clients resolving that internal address.

![UniFi local DNS record for the NetBird host](../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S06-UniFi-Internal-DNS-Record-2026-07-11.jpg)

## What I Checked After Each Step

- Web traffic returned HTTP `200` or the expected registry `401`.
- `ntpdig` exited `0` through UDP 123.
- Direct external DNS to `<YOUR_EXTERNAL_DNS_IP>:53` timed out under the final block.
- Security-A services returned their expected HTTP codes & listeners.
- The final UniFi dashboard remained healthy after Cluster-Net was added.

![UniFi state after the Cluster-Net change](../Infrastructure/Compute/Galaxy/Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Network-Segmentation-Cluster-Net-Postchange-UniFi-Dashboard-2026-07-10.png)

## Troubleshooting and Recovery

Rule order matters. If the catch-all block sits above the two allows, HTTPS & NTP fail together. If only the hostname fails, check the local DNS record before changing firewall state. Roll back one policy or DNS record at a time & repeat the same test that failed.

## Known Limits

The broader segmentation plan still contains deferred networks & source-group tightening. The guide covers the completed Security-A, Cluster-Net, & Access-A work.

## Source Records

- [UniFi configuration index](../Infrastructure/Network/UniFi/README.md)
- [Security-A migration](../Infrastructure/Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md)
- [Segmentation plan](../Infrastructure/Network/UniFi/Documentation/Change%20Plans/Network-Segmentation-TODO.md)
- [Access-A deployment](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Docker-Network%20LXC%20Deployment%20-%202026-07-10.md)
