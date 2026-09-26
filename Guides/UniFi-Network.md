# UniFi Network Walkthrough

**Created:** 2026-07-20  
**Last updated:** 2026-09-25

## What This Guide Covers

This guide follows the network work that supports Galaxy and the hosted platforms: VLANs, firewall zones, the Security-A migration, the Access-A egress rules, local DNS, the identity-zone ordering fix, and the switch-port checks needed for Corosync VLAN 71.

## Current Status and Verified Versions

Verified against the controller on 2026-09-24. UniFi Network 10.6.106 holds 23 networks: 16 routed corporate LANs, two WANs, the ProtonVPN client network, and four remote-user VPN servers, of which only `Management Access` is enabled. The 16 LANs sit in 12 zones. Cluster-Net (VLAN 71) shares AlphaSec-Mgmt with MGMT-A; Security-A (72) and MONITOR-A (73) share AlphaSec-Observability. The second WAN is configured for failover but had no link or address.

UniFi holds 30 static local DNS records: 24 names at `192.168.85.2`, one for each live Nginx Proxy Manager host, five Proxmox node names on MGMT-A, and `hq-mgt01.ad.alphasecunited.com` on IDENTITY-A. The last full policy count, on 2026-09-20, was 89 user-defined firewall policies, 81 allows and eight blocks.

## What You Need

- Administrator access to the UniFi controller.
- A current export or screenshot of the affected VLAN, zone, port, and firewall tables.
- Console access to any Proxmox node whose management or Corosync path will change.
- The exact source, destination, protocol, and port list for each policy.

## How the Pieces Fit Together

![UniFi VLAN segmentation and firewall zones fed by the switch trunk](../Assets/Diagrams/unifi-network.svg)

## Walkthrough

### Step 1: Record VLANs and Zones

I start with the current [VLAN inventory](../Infrastructure/Network/UniFi/Configuration/network-vlan.md) and [zone inventory](../Infrastructure/Network/UniFi/Configuration/zone.md). A VLAN ID, subnet, gateway, DHCP state, and zone assignment must agree before I write a policy against it.

### Step 2: Verify Switch Trunks

For Cluster-Net on 2026-07-10, I checked all four Proxmox switch ports before adding `vmbr0.71`. VLAN 71 was already tagged to grey, purple, and blue; red needed the VLAN admitted before its host interface could communicate.

![UniFi state before the Cluster-Net change](../Infrastructure/Compute/Galaxy/Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Network-Segmentation-Cluster-Net-Prechange-UniFi-Dashboard-2026-07-10.png)

### Step 3: Migrate the Security Services

On 2026-07-12 I moved Wazuh, Prometheus, Grafana, Splunk, HEC, and SC4S from the earlier management addresses into Security-A. I updated the guest addresses, DNS or client targets, and firewall destinations in the same change, then checked every listener from an allowed source. Prometheus and Grafana later moved again, to `monitor-01` on MONITOR-A, on 2026-07-26.

### Step 4: Add Ordered Access-A Egress

I created three Access-to-External rules in this order:

1. Allow TCP 80 and 443 from the permitted Access-A service addresses.
2. Allow UDP 123 from those same addresses.
3. Block the remaining Access-A traffic to External.

The current rules use `PG-Egress-Web` and `PG-NTP`. The reverse proxy itself is represented by `AG-Reverse-Proxy` in its cross-zone policies.

![Access-A egress rules after deployment](../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S05A-UniFi-Access-A-Egress-Policies-After-2026-07-11.jpg)

### Step 5: Add Local DNS

I added `netbird.alphasecunited.com` as an A record for `192.168.85.2` with TTL 300. The browser path, NPM certificate, and NetBird HTTPS check all depend on clients resolving that internal address. Every internal HTTPS name since has followed the same pattern, an A record at `192.168.85.2` per NPM proxy host.

![UniFi local DNS record for the NetBird host](../Platforms/Netbird/Evidence/Docker-Network%20Access%20Stack%20Deployment%20-%202026-07-10/Screenshots/S06-UniFi-Internal-DNS-Record-2026-07-11.jpg)

### Step 6: Order Identity Egress and Point Clients at the Domain Controllers

The Active Directory build on VLAN 65 needed two gateway changes on 2026-09-09. Neither added a capability: one fixed rule order, the other moved DNS.

The identity zone had three policies to External: an allow for TCP 80 and 443, an allow for UDP 123, and a catch-all block. The NTP allow sat below the block, so it never ran, and the controller holding the PDC emulator role fell back to its own CMOS clock. Every machine in the domain inherits that drift. Moving the NTP allow above the block is the whole fix. The saved order after reload is `Allow Identity Web Egress` at index 10000, `Allow Identity NTP Egress` at 10001, then `Block Identity Other External Egress` at 10002.

![Identity to External policy order](../Infrastructure/Network/UniFi/Evidence/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09/Screenshots/01-Firewall-Order.png)

Then DHCP DNS on the two client networks moved from automatic to the two domain controllers, `192.168.65.10` first and `192.168.65.11` second. Domain members have to resolve through the domain controllers; pointing them at the gateway breaks service location lookups.

![Secure VLAN 50 DNS servers](../Infrastructure/Network/UniFi/Evidence/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09/Screenshots/02-Secure-DNS.png)

![Secure Client VLAN 60 DNS servers](../Infrastructure/Network/UniFi/Evidence/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09/Screenshots/03-Secure-Client-DNS.png)

Check the firewall before assuming the DNS change is enough. Both client networks sit in the Internal zone and the controllers sit in the identity zone, so the traffic crosses a zone boundary where the default is a block. In my case an existing policy already covered it, matching the two client networks as source and an address group of the two controllers on the domain-member port set. Verify that path exists rather than adding a second rule for it, and be careful reading a filtered policy list: the controller returns a capped page, so a rule can be absent from the list and present on the gateway.

Afterwards `w32tm /query /source` on the PDC named an external server instead of `Local CMOS Clock`, and the two downstream hosts followed the domain hierarchy at stratum 5 and 6.

## What I Checked After Each Step

- Web traffic returned HTTP `200` or the expected registry `401`.
- `ntpdig` exited `0` through UDP 123.
- Direct external DNS to `1.1.1.1:53` timed out under the final block.
- Security-A services returned their expected HTTP codes and listeners.
- The final UniFi dashboard remained healthy after Cluster-Net was added.

![UniFi state after the Cluster-Net change](../Infrastructure/Compute/Galaxy/Evidence/Cluster-Net%20Corosync%20Link%20Addition%20-%202026-07-10/Screenshots/Network-Segmentation-Cluster-Net-Postchange-UniFi-Dashboard-2026-07-10.png)

## Troubleshooting and Recovery

Rule order matters. If the catch-all block sits above the two allows, HTTPS and NTP fail together. If only the hostname fails, check the local DNS record before changing firewall state. Roll back one policy or DNS record at a time and repeat the same test that failed.

## Known Limits

The steps cover the Security-A, Cluster-Net, Access-A, consolidation, and identity work. UniFi Threat Management inspects only part of the 16 LANs; the open coverage question is in [TODO.md](../TODO.md).

## Source Records

- [UniFi configuration index](../Infrastructure/Network/UniFi/README.md)
- [Security-A migration](../Infrastructure/Network/UniFi/Documentation/Change%20Records/Security-A%20Migration%20-%202026-07-12.md)
- [Zone and object consolidation](../Infrastructure/Network/UniFi/Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md)
- [Access-A deployment](../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Docker-Network%20LXC%20Deployment%20-%202026-07-10.md)
- [Local DNS inventory](../Infrastructure/Network/UniFi/Configuration/local-dns.md)
- [Identity NTP and client DNS](../Infrastructure/Network/UniFi/Documentation/Change%20Records/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09.md)
- [Active Directory guide](Active-Directory.md) for the forest these two changes serve
