# UniFi Network

**Created:** 2026-07-09  
**Last updated:** 2026-09-05

I track UniFi-owned VLANs, zones, firewall rules, DNS records, network objects, VPNs, and port profiles here. Host firewall and Proxmox Datacenter configuration stays with the Galaxy compute records.

A controller readback on 2026-09-05 returned 22 network objects: 15 routed corporate LANs, two WANs, one ProtonVPN client network, and four remote-user VPN networks. It also returned 11 firewall zones, 68 user-defined policies split 61 allows to seven blocks, and five WLANs. The 2026-08-19 readback after the Kasm retirement is the last full count of the rest: 15 reusable firewall groups, 15 client groups, four OON policies, one traffic route, five switch port profiles, and 27 enabled local DNS records. Three WLANs are enabled and two are disabled.

The remaining traffic route is `VPN - Proton`. It is enabled with its kill switch on and targets `Proton-WiFi`/VLAN 45 through the retained ProtonVPN client.

## Configuration Records

- [Networks and VLANs](Configuration/network-vlan.md)
- [Galaxy PXE provisioning service (2026-07-30)](../../../Platforms/Galaxy%20PXE/Documentation/Change%20Records/Galaxy%20PXE%20Provisioning%20Service%20-%202026-07-30.md)
- [Firewall zones](Configuration/zone.md)
- [Firewall policies](Configuration/firewall.md)
- [Local DNS](Configuration/local-dns.md)
- [Network objects](Configuration/objects.md)
- [VPNs, network groups, and port profiles](Configuration/vpn-networks-port-profiles.md)
- [Proton-WiFi VLAN 45 (2026-08-10)](Documentation/Change%20Records/Proton-WiFi%20VLAN%2045%20-%202026-08-10.md)
- [edge-01 move to DMZ VLAN 30 (2026-08-07)](Documentation/Change%20Records/edge-01%20Move%20to%20DMZ%20VLAN%2030%20-%202026-08-07.md)
- [Zone and object consolidation (2026-07-27)](Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md)
- [Firewall audit (2026-07-27)](../../../Security/Assessments/UniFi%20Firewall%20Audit%20-%202026-07-27.md)
- [MGMT-A final lockdown (2026-07-27)](Documentation/Change%20Records/MGMT-A%20Final%20Lockdown%20-%202026-07-27.md)
- [Troubleshooting index](Documentation/Troubleshooting/README.md)

## Retired Kasm Records

- [Kasm Workspaces decommission (2026-08-19)](../../../Archive/Platforms/Kasm%20Workspaces/Documentation/Change%20Records/Kasm%20Workspaces%20Decommission%20-%202026-08-19.md)
- [Kasm lab network simplification (2026-07-23)](../../../Archive/Infrastructure/Network/UniFi/Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md)
- [Kasm network build evidence (2026-07-22, superseded)](../../../Archive/Infrastructure/Network/UniFi/Evidence/Kasm%20Security%20Lab%20Network%20-%202026-07-22/Evidence-Index.md)
- [Kasm firewall audit (2026-07-22, superseded)](../../../Archive/Security/Assessments/UniFi%20Kasm%20Firewall%20Audit%20-%202026-07-22.md)

## Physical Power

I record Ahsoka Gateway (`UCG-Fiber`), Bane Switch POE (`USW-Pro-Max-16-PoE`), & the Verizon ONT on `UPS-02` in the [power equipment inventory](../../Hardware/Power.md). `UPS-02` is an APC Back-UPS RS 1500MS2 rated for 1500 VA / 900 W.
