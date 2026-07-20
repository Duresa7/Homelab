# UniFi Object-Oriented Networking Policies

**Created:** 2026-07-09  
**Last updated:** 2026-07-20

## How I Use UniFi Objects

I build UniFi policies from clients, groups, networks, zones, regions, applications, & IP or port groups. The controller turns those object references into the firewall, ACL, routing, QoS, & zone configuration enforced by the gateway, switches, and access points.

An object-based rule follows its membership. If a client changes address or moves between groups, I update the object instead of rewriting every policy that uses it.

## OON Policies

| Policy | Enabled | Target Type | Applies To | Action |
|---|---|---|---|---|
| Proton OON | Disabled | Clients | 3 MACs: `<YOUR_VPN_CLIENT_MAC_C>`, `<YOUR_VPN_CLIENT_MAC_A>`, `<YOUR_VPN_CLIENT_MAC_B>` | Route all traffic → ProtonVPN (kill switch on) |
| PC 1 | Disabled | Client | 1 MAC: `<YOUR_MEDIA_HOST_MAC>` | QoS: prioritize all traffic (always) |
| isolate | Disabled | Network | DMZ (VLAN 30) | Route all traffic → ProtonVPN (kill switch on) |
| QoS for D | Enabled | Group | D_devices (5 clients) | QoS: prioritize all traffic (always) |

Four policies exist, and only `QoS for D` is enabled. `Proton OON` and `isolate` route through ProtonVPN with a kill switch when enabled; both are currently disabled.
