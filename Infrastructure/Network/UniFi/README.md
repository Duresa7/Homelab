# UniFi Network

**Created:** 2026-07-09  
**Last updated:** 2026-09-19

I track UniFi-owned VLANs, zones, firewall rules, DNS records, networks, Network Lists, VPNs, and port profiles here. Host firewall and Proxmox Datacenter configuration stays with the Galaxy compute records.

On 2026-09-07 I verified the identity preparation and completed its trunk and Splunk path. That readback returned 23 networks (16 routed corporate LANs), 12 zones, 22 Network Lists, and 77 user-defined policies (69 allows and eight blocks), with 351 total policies including generated rules. On 2026-09-16 the controller returns 12 zones, 22 Network Lists, 29 static DNS records, and 86 user-defined policies split 78 allows to eight blocks, with 85 enabled. On 2026-09-19 I added `Allow Identity to App Portal`, taking the user-defined total to 87, split 79 allows to eight blocks; it admits `HQ-WS001` alone to the portal's listener on `docker-main`. A second rule the same day, `Allow Secure to HQ-WS001 SSH`, took the total to 88, split 80 allows to eight blocks; it admits Secure (VLAN 50) to that workstation on TCP 22. Later that evening I put App Portal behind Nginx Proxy Manager at `appportal.alphasecunited.com`, replaced `Allow Identity to App Portal` with `Allow HQ-WS001 to NPM HTTPS`, and added TCP 3004 to the NPM-to-docker-main policy: the user-defined total is 88 again, split 80 allows to eight blocks, and static DNS records rose to 30. Proxmox-Trunk now carries VLANs 65 and 60 to grey-server on Bane Switch POE port 14. I retained the [identity readback](Evidence/Identity%20Plane%20Network%20Preparation%20-%202026-09-07/Final%20Identity%20Policy%20Readback.json) and updated the four configuration views below.

A full controller readback on 2026-09-06 returned 22 networks: 15 routed corporate LANs, two WANs, one ProtonVPN client network, and four remote-user VPN networks. It also returned 11 firewall zones, 68 user-defined policies split 61 allows to seven blocks, 16 reusable Network Lists, 17 client groups (16 after I deleted the empty `IOT` duplicate later that day), four OON policies, one traffic route, five switch port profiles, five WLANs with three enabled, 29 enabled local DNS records, no port forwards, and no user-defined static routes. Five adopted devices were online: the gateway, three switches, and one access point, on Network application 10.6.101. Against the 2026-08-19 count, the Network Lists gained `PG-Printing`, the client groups gained an `IOT` and an `IoT` entry, and local DNS gained `mcp` and `openwebui`. The configuration records below carry the detail.

The remaining traffic route is `VPN - Proton`. It is enabled with its kill switch on and targets `Proton-WiFi`/VLAN 45 through the retained ProtonVPN client.

On 2026-09-09 I verified Identity external egress in Web, NTP, Block order and DHCP DNS on Secure and Secure Client as 192.168.65.10, then 192.168.65.11. The [change record and screenshots](Documentation/Change%20Records/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09.md) retain the saved states.

## Configuration Records

- [Networks and VLANs](Configuration/network-vlan.md)
- [Galaxy PXE provisioning service (2026-07-30)](../../../Platforms/Galaxy%20PXE/Documentation/Change%20Records/Galaxy%20PXE%20Provisioning%20Service%20-%202026-07-30.md)
- [Firewall zones](Configuration/zone.md)
- [Firewall policies](Configuration/firewall.md)
- [Local DNS](Configuration/local-dns.md)
- [Policy features and Network Lists](Configuration/objects.md)
- [VPNs, Network Lists, and port profiles](Configuration/vpn-networks-port-profiles.md)
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
