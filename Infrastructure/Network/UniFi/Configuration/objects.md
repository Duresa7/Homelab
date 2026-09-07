# UniFi Policy Features and Network Lists

**Created:** 2026-07-09  
**Last updated:** 2026-09-07

## How I Build UniFi Policies

I use Network Lists for reusable address and port selectors in firewall policies. I track OON Policies, traffic routes, and Client Groups separately below.

A firewall policy that references a Network List follows its membership. When an address changes, I update the Network List and check every policy that references it.

Three separate features carry the word "object" in this interface and they are not interchangeable. The Objects entry in the Policy Engine navigation opens the OON policy list, not the address and port groups. The `AG-` and `PG-` groups appear as Network Lists, which define IP addresses, subnets, domains, and ports for use in policies, and I reach them from inside the firewall policy editor when a rule selects IP or List rather than from that navigation entry. Client groups are a third feature again, keyed on MAC. I use Network List, OON Policy, and Client Group to distinguish these features.

On 2026-07-31 I reused `AG-Proxmox-Nodes` as the source for `Allow Proxmox Nodes to Galaxy PXE`. Future Galaxy nodes gain the post-cutover TCP 8080 callback path when I add their management address to this Network List. The VLAN 5 phase remains covered by the separate `Server-Provision` network.

On 2026-09-07 I renamed the six `OBJ-` address groups to `AG-`, changing only their names; I verified unchanged IDs and members (1, 1, 2, 5, 3, and 1 in table order), all six requested `AG-` names, zero `OBJ-` names, and all ten existing port groups unchanged. The later policy check confirmed the same group-ID references and unchanged returned configurations in all 23 original referencing policies. I did not retain a separate raw transcript.

The final same-day readback returned 22 Network Lists and 349 firewall policies, including 76 user-defined policies. Six Network Lists appeared between checks: `AG-Domain-Controllers`, `AG-Identity-Servers`, `AG-PAW`, `PG-AD-Client`, `PG-Windows-Admin`, and `PG-Windows-Exporter`. A new `Allow Monitor to Windows Exporter` policy also references `AG-Monitor-Collector`. I made none of those additions and changed no policies during this rename; the six renamed groups and the ten original port groups still matched their verified IDs and memberships.

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
| VPN - Proton | Yes | Internet | Network: Proton-WiFi (VLAN 45) |

I deleted `Non-tracking` before deleting Secure-V/VLAN 100. I deleted `KASM Lab Proton Egress` before removing its target network on 2026-08-19. The controller now returns one traffic route and no reference to either retired network.

## Network Lists

These are the Network Lists in the interface. The API calls them `address-group` and `port-group`, and a policy references one through `ip_group_id` or `port_group_id`.

The table below covers the 16 Network Lists present at the rename verification on 2026-09-07: six IPv4 address groups and ten port groups.

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
| Portainer Edge Agents | Port | 8000, 9443 |
| Allow Identity Sync Service Connection-9543 | Port | 9543 |
| PG-Node-Exporter | Port | 9100, 9101, 9102 |
| PG-Egress-Web | Port | 80, 443 |
| PG-NTP | Port | 123 |
| PG-Galaxy-PXE-Callback | Port | 8080 |
| PG-Printing | Port | 631, 9100 |

On 2026-09-02 I added 9102 to `PG-Node-Exporter` for What's Up Docker, so the three monitoring policies that reference the group admit the new exporter without their own edit.

`PG-Printing` carries IPP on 631 and raw printing on 9100 for `Allow Internal to Printer`. It was on the controller but absent from this table until the 2026-09-06 readback, the same way its policy was absent from the firewall table until 2026-08-31.

I moved 35 exact selectors across 24 policies onto these Network Lists. I kept 11 partial or mixed selectors inline because replacing them with a broader group would change behavior.

`AG-Galaxy-PXE-Service` and `PG-Galaxy-PXE-Callback` are single-member groups, which I normally avoid. I created them on 2026-07-31 because the same literal `192.168.40.36:8080` destination was duplicated across both Galaxy PXE policies. Two policies carrying the same hardcoded service is the duplication these Network Lists exist to remove: if the PXE service ever moves off `ansible-01` or gains a second listener, I edit one Network List instead of hunting two rules. Both policies reference these Network Lists for their destination; their sources are `AG-Proxmox-Nodes` and the `Server-Provision` network. All five nodes returned `ok` with HTTP 200 from the health endpoint after the 2026-07-31 change.

## Client Groups

Sixteen client groups exist as of 2026-09-06. The readback that morning returned 17: the 15 below plus an empty `IOT` and a one-member `IoT`, both created on 2026-08-26 within nine seconds of each other, the same afternoon as the `PG-Printing` group and its policy. `IoT` holds the Brother printer at `192.168.20.212`, the destination `Allow Internal to Printer` names, so it is the group made for that work and it stays. `IOT` was the empty first attempt at the name, the same name as the empty group I removed on 2026-07-27, and I deleted it the same day; see [Empty IOT Client Group Removal](../Documentation/Change%20Records/Empty%20IOT%20Client%20Group%20Removal%20-%202026-09-06.md).

| Group | Members | Current use or decision |
|---|---:|---|
| grey-node-and-guests | 5 | Physical `grey-node`, `docker-main`, and three retired guest MACs |
| family_devices | 15 | Household group |
| D_devices | 5 | Target of enabled OON policy `QoS for D` |
| ilyas_device | 2 | Household group |
| Ahmed Devices | 4 | Household group |
| ifitu devices | 2 | Household group |
| sedia_devices | 2 | Household group |
| iot_device | 6 | Populated IoT group |
| guest_device | 1 | Guest group |
| Admin_Device | 4 | Approved administrative devices |
| docker-blue | 1 | LXC 108 |
| VM | 1 | `security-01`; I removed the retired Kasm VM member on 2026-08-19 |
| blue server | 0 | Empty retained group |
| green-server | 1 | Physical Green node |
| LXC | 1 | LXC member group |
| IoT | 1 | The Brother printer on IoT/VLAN 20, created 2026-08-26 with the printing policy |

I deleted the empty `IOT` group and the obsolete `Game Servers` group after the S01 and final reference scans found no firewall or OON dependency. I renamed `server` to `docker-blue` and `grey-server` to `grey-node-and-guests` without changing membership.

On 2026-08-19 I removed the retired Kasm client from `VM`, reducing that group from two members to one, and used the controller's forget action on the offline historical client record. No firewall policy or OON Policy depended on that member.

`Device Access to Proxmox` still carries the four administrative MACs inline. The V2 policy selector schema has no client-group target, so I did not replace those selectors with `Admin_Device`.

On 2026-08-07 I added `3128` to `Proxmox-Admin-Ports` for the Proxmox SPICE proxy. This is the payoff for the group existing: one edit gave all four administrative devices the port, with no new policy and no reordering. The Proxmox datacenter firewall needed the same port separately, because these two firewalls are enforced independently. The complete record is [SPICE Console Firewall Access - 2026-08-07](../../../Compute/Galaxy/Documentation/Change%20Records/SPICE%20Console%20Firewall%20Access%20-%202026-08-07.md).

The exact before-and-after membership and the reference checks are retained with [Zone and Object Consolidation - 2026-07-27](../Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md).
