# UniFi Network

**Created:** 2026-07-09  
**Last updated:** 2026-08-10

I track UniFi-owned VLANs, zones, firewall rules, DNS records, network objects, VPNs, and port profiles here. Host firewall and Proxmox Datacenter configuration stays with the Galaxy compute records.

The last full controller count on 2026-07-30 was 28 network objects, 20 routed LAN networks, 14 firewall zones, 361 policies, 13 reusable firewall groups, 12 client groups, four OON policies, two traffic routes, four WLANs, and five switch port profiles. The user-defined firewall inventory reached 131 on 2026-08-10 after I added the narrow NPM-to-CLI-Proxy path. The local DNS inventory now contains 23 enabled internal NPM names and one disabled apex record.

## Configuration Records

- [Networks and VLANs](Configuration/network-vlan.md)
- [Galaxy PXE provisioning service (2026-07-30)](../../../Platforms/Galaxy%20PXE/Documentation/Change%20Records/Galaxy%20PXE%20Provisioning%20Service%20-%202026-07-30.md)
- [Firewall zones](Configuration/zone.md)
- [Firewall policies](Configuration/firewall.md)
- [Local DNS](Configuration/local-dns.md)
- [Network objects](Configuration/objects.md)
- [VPNs, network groups, and port profiles](Configuration/vpn-networks-port-profiles.md)
- [Zone and object consolidation (2026-07-27)](Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md)
- [Firewall audit (2026-07-27)](../../../Security/Assessments/UniFi%20Firewall%20Audit%20-%202026-07-27.md)
- [MGMT-A final lockdown (2026-07-27)](Documentation/Change%20Records/MGMT-A%20Final%20Lockdown%20-%202026-07-27.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)
- [Kasm lab network simplification (2026-07-23)](Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md)
- [Kasm network build evidence (2026-07-22, superseded)](Evidence/Kasm%20Security%20Lab%20Network%20-%202026-07-22/Evidence-Index.md)
- [Kasm firewall audit (2026-07-22, superseded)](../../../Security/Assessments/UniFi%20Kasm%20Firewall%20Audit%20-%202026-07-22.md)

## Physical Power

I record Ahsoka Gateway (`UCG-Fiber`), Bane Switch POE (`USW-Pro-Max-16-PoE`), & the Verizon ONT on `UPS-02` in the [power equipment inventory](../../Hardware/Power.md). `UPS-02` is an APC Back-UPS Pro BR1500MS2 rated for 1500 VA / 900 W.
