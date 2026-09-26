# UniFi Policy Features and Network Lists

**Created:** 2026-07-09  
**Last updated:** 2026-09-25

This file holds the reusable policy objects: 22 Network Lists (ten IPv4 address groups and 12 port groups), four OON policies, one traffic route and 16 client groups.

**Last verified against the controller:** Network Lists on 2026-09-16, when I removed the Portainer Edge Agents port group ([Policy and DNS Readback](../Documentation/Change%20Records/Policy%20and%20DNS%20Readback%20-%202026-09-16.md)); OON policies, traffic routes and client groups on 2026-09-06.

## How I Build UniFi Policies

I use Network Lists for reusable address and port selectors in firewall policies. I track OON Policies, traffic routes, and Client Groups separately below.

A firewall policy that references a Network List follows its membership. When an address changes, I update the Network List and check every policy that references it.

Three separate features carry the word "object" in this interface and they are not interchangeable. The Objects entry in the Policy Engine navigation opens the OON policy list, not the address and port groups. The `AG-` and `PG-` groups appear as Network Lists, which define IP addresses, subnets, domains, and ports for use in policies, and I reach them from inside the firewall policy editor when a rule selects IP or List rather than from that navigation entry. Client groups are a third feature again, keyed on MAC. I use Network List, OON Policy, and Client Group to distinguish these features.

`AG-Proxmox-Nodes` is the source of `Allow Proxmox Nodes to Galaxy PXE`, so a new Galaxy node gains the TCP 8080 callback path when I add its management address to that list. The VLAN 5 phase is covered by the `Server-Provision` network.

## OON Policies

| Policy | Enabled | Target Type | Applies To | Action |
|---|---|---|---|---|
| Proton OON | Disabled | Clients | 3 MACs: `<REDACTED_VPN_CLIENT_MAC_C>`, `<REDACTED_VPN_CLIENT_MAC_A>`, `<REDACTED_VPN_CLIENT_MAC_B>` | Route all traffic → ProtonVPN (kill switch on) |
| PC 1 | Disabled | Client | 1 MAC: `<REDACTED_MEDIA_HOST_MAC>` | QoS: prioritize all traffic (always) |
| isolate | Disabled | Network | DMZ (VLAN 30) | Route all traffic → ProtonVPN (kill switch on) |
| QoS for D | Enabled | Group | D_devices (5 clients) | QoS: prioritize all traffic (always) |

Four policies exist, and only `QoS for D` is enabled. `Proton OON` and `isolate` route through ProtonVPN with a kill switch when enabled; both are currently disabled.

## Traffic Routes

Traffic routes are separate from the OON policies above. One remains and points to the `ProtonVPN` client network with the kill switch on.

| Route | Enabled | Match | Target |
|---|---|---|---|
| VPN - Proton | Yes | Any Internet destination through the `ProtonVPN` client, kill switch on | Network: Proton-WiFi (VLAN 45) |

`VPN - Proton` has targeted `Proton-WiFi`/VLAN 45 since 2026-08-10 ([Proton-WiFi VLAN 45](../Documentation/Change%20Records/Proton-WiFi%20VLAN%2045%20-%202026-08-10.md)). The retired `Non-tracking` and `KASM Lab Proton Egress` routes were deleted on 2026-07-27 and 2026-08-19.

## Network Lists

These are the Network Lists in the interface. The API calls them `address-group` and `port-group`, and a policy references one through `ip_group_id` or `port_group_id`.

The table covers all 22 Network Lists the controller returned on 2026-09-16. The six identity groups and their IDs are in the 2026-09-07 [group readback](../Evidence/Identity%20Plane%20Network%20Preparation%20-%202026-09-07/Exports/Initial%20Controller%20Readback.json).

| Group | Type | Members |
|---|---|---|
| AG-Monitor-Collector | IPv4 | 192.168.73.2 |
| AG-Reverse-Proxy | IPv4 | 192.168.85.2 |
| AG-Security-Stack | IPv4 | 192.168.72.2, 192.168.72.3 |
| AG-Proxmox-Nodes | IPv4 | 192.168.70.10 through 192.168.70.14 |
| AG-Observability-Hosts | IPv4 | 192.168.72.2, 192.168.72.3, 192.168.73.2 |
| AG-Galaxy-PXE-Service | IPv4 | 192.168.40.36 |
| Wazuh Ports | Port | 1514, 1515 |
| App Access | Port | 80, 8000 |
| Proxmox-Admin-Ports | Port | 22, 8006, 3128 |
| Allow Identity Sync Service Connection-9543 | Port | 9543 |
| PG-Node-Exporter | Port | 9100, 9101, 9102 |
| PG-Egress-Web | Port | 80, 443 |
| PG-NTP | Port | 123 |
| PG-Galaxy-PXE-Callback | Port | 8080 |
| PG-Printing | Port | 631, 9100 |
| AG-Domain-Controllers | IPv4 | 192.168.65.10, 192.168.65.11 |
| AG-Identity-Servers | IPv4 | 192.168.65.10, 192.168.65.11, 192.168.65.12 |
| AG-PAW | IPv4 | 192.168.50.241 |
| PG-AD-Client | Port | 53, 88, 123, 135, 389, 445, 464, 636, 3268, 3269, 49152-65535 |
| PG-Windows-Admin | Port | 22, 3389, 5985, 5986 |
| PG-Windows-Exporter | Port | 9182 |
| AG-Automation-Hosts | IPv4 | 192.168.40.179, 192.168.40.39 |

`Wazuh Ports` holds exactly 1514 and 1515. Port groups hold port numbers only; `Allow Workstations to AD` applies `PG-AD-Client` over TCP and UDP. `Allow Identity Web Egress` names TCP 80 and 443 inline, because the controller rejected a port group with an any-in-zone destination.

`PG-Node-Exporter` carries 9102 for What's Up Docker since 2026-09-02, so the monitoring policies that reference it needed no edit of their own.

`PG-Printing` carries IPP on 631 and raw printing on 9100 for `Allow Internal to Printer`.

The 2026-07-27 consolidation moved 35 exact selectors across 24 policies onto these lists and kept 11 partial or mixed selectors inline, because a broader group would have changed behavior.

`AG-Galaxy-PXE-Service` and `PG-Galaxy-PXE-Callback` are single-member groups, which I normally avoid. Both Galaxy PXE policies use them as their destination, so if the PXE service moves off `ansible-01` or gains a second listener I edit one list instead of two rules. The sources are `AG-Proxmox-Nodes` and the `Server-Provision` network.

## Client Groups

Sixteen client groups existed on the 2026-09-06 readback, after I deleted an empty duplicate `IOT` group that day ([Empty IOT Client Group Removal](../Documentation/Change%20Records/Empty%20IOT%20Client%20Group%20Removal%20-%202026-09-06.md)).

| Group | Members | Current use or decision |
|---|---:|---|
| grey-node-and-guests | 5 | Physical `grey-node`, `docker-main`, and three retired guest MACs |
| family_devices | 15 | Household group |
| D_devices | 5 | Target of enabled OON policy `QoS for D` |
| IK-user Devices | 2 | Household group |
| AH-user Devices | 4 | Household group |
| ifitu devices | 2 | Household group |
| sedia_devices | 2 | Household group |
| iot_device | 6 | Populated IoT group |
| guest_device | 1 | Guest group |
| Admin_Device | 4 | My administrative devices |
| docker-blue | 1 | LXC 108 |
| VM | 1 | `security-01`; I removed the retired Kasm VM member on 2026-08-19 |
| blue server | 0 | Empty retained group |
| green-server | 1 | Physical Green node |
| LXC | 1 | LXC member group |
| IoT | 1 | The Brother printer on IoT/VLAN 20, created 2026-08-26 with the printing policy |

`Device Access --> Proxmox` carries five client MACs inline: the four administrative devices and `ubuntu-dev`. The V2 policy selector schema has no client-group target, so `Admin_Device` cannot replace them.

`Proxmox-Admin-Ports` gained 3128 for the SPICE proxy on 2026-08-07; the Proxmox Datacenter firewall needed the same port separately. [SPICE Console Firewall Access](../../../Compute/Galaxy/Documentation/Change%20Records/SPICE%20Console%20Firewall%20Access%20-%202026-08-07.md).

The exact before-and-after membership and the reference checks are retained with [Zone and Object Consolidation - 2026-07-27](../Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md).
