# UniFi Object-Oriented Networking Policies

**Created:** 2026-07-09  
**Last updated:** 2026-07-31

## How I Use UniFi Objects

I build UniFi policies from clients, groups, networks, zones, regions, applications, & IP or port groups. The controller turns those object references into the firewall, ACL, routing, QoS, & zone configuration enforced by the gateway, switches, and access points.

An object-based rule follows its membership. If a client changes address or moves between groups, I update the object instead of rewriting every policy that uses it.

On 2026-07-31 I reused `OBJ-Proxmox-Nodes` as the source for `Allow Proxmox Nodes to Galaxy PXE`. Future Galaxy nodes gain the post-cutover TCP 8080 callback path when I add their management address to this object. The VLAN 5 phase remains covered by the separate `Server-Provision` network object.

## OON Policies

| Policy | Enabled | Target Type | Applies To | Action |
|---|---|---|---|---|
| Proton OON | Disabled | Clients | 3 MACs: `<REDACTED_VPN_CLIENT_MAC_C>`, `<REDACTED_VPN_CLIENT_MAC_A>`, `<REDACTED_VPN_CLIENT_MAC_B>` | Route all traffic → ProtonVPN (kill switch on) |
| PC 1 | Disabled | Client | 1 MAC: `<REDACTED_MEDIA_HOST_MAC>` | QoS: prioritize all traffic (always) |
| isolate | Disabled | Network | DMZ (VLAN 30) | Route all traffic → ProtonVPN (kill switch on) |
| QoS for D | Enabled | Group | D_devices (5 clients) | QoS: prioritize all traffic (always) |

Four policies exist, and only `QoS for D` is enabled. `Proton OON` and `isolate` route through ProtonVPN with a kill switch when enabled; both are currently disabled.

## Traffic Routes

Traffic routes are separate from the OON policies above. Two remain. Both point to the `ProtonVPN` client network with the kill switch on.

| Route | Enabled | Match | Target |
|---|---|---|---|
| VPN - Proton | No | Internet | 1 device |
| KASM Lab Proton Egress | Yes | Internet | Network: KASM-BROWSER (VLAN 74) |

I deleted `Non-tracking` before deleting Secure-V/VLAN 100. The controller now returns two traffic routes and no reference to the retired network.

## Address and Port Groups

Fifteen reusable firewall groups exist: six IPv4 address groups and nine port groups.

| Group | Type | Members |
|---|---|---|
| OBJ-Monitor-Collector | IPv4 | 192.168.73.2 |
| OBJ-Reverse-Proxy | IPv4 | 192.168.85.2 |
| OBJ-Security-Stack | IPv4 | 192.168.72.2, 192.168.72.3 |
| OBJ-Proxmox-Nodes | IPv4 | 192.168.70.10 through 192.168.70.14 |
| OBJ-Observability-Hosts | IPv4 | 192.168.72.2, 192.168.72.3, 192.168.73.2 |
| OBJ-Galaxy-PXE-Service | IPv4 | 192.168.40.36 |
| Wazuh Ports | Port | 1514, 1515 |
| App Access | Port | 80, 8000 |
| Proxmox-Admin-Ports | Port | 22, 8006 |
| Portainer Edge Agents | Port | 8000, 9443 |
| Allow Identity Sync Service Connection-9543 | Port | 9543 |
| PG-Node-Exporter | Port | 9100, 9101 |
| PG-Egress-Web | Port | 80, 443 |
| PG-NTP | Port | 123 |
| PG-Galaxy-PXE-Callback | Port | 8080 |

I moved 35 exact selectors across 24 policies onto these objects. I kept 11 partial or mixed selectors inline because replacing them with a broader group would change behavior.

`OBJ-Galaxy-PXE-Service` and `PG-Galaxy-PXE-Callback` are single-member groups, which I normally avoid. I created them on 2026-07-31 because the same literal `192.168.40.36:8080` destination was duplicated across both Galaxy PXE policies. Two policies carrying the same hardcoded service is the duplication these objects exist to remove: if the PXE service ever moves off `ansible-01` or gains a second listener, I edit one object instead of hunting two rules. Both policies now reference objects on the source and the destination side, and all five nodes still returned `ok` with HTTP 200 from the health endpoint after the change.

## Client Groups

Twelve client groups remain.

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
| VM | 2 | `security-01` and `kasm-01`; retained because Kasm is out of scope |

I deleted the empty `IOT` group and the obsolete `Game Servers` group after the S01 and final reference scans found no firewall or OON dependency. I renamed `server` to `docker-blue` and `grey-server` to `grey-node-and-guests` without changing membership.

`Device Access to Proxmox` still carries the four administrative MACs inline. The V2 policy selector schema has no client-group target, so I did not replace those selectors with `Admin_Device`.

The exact before-and-after membership and the reference checks are retained with [Zone and Object Consolidation - 2026-07-27](../Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md).
