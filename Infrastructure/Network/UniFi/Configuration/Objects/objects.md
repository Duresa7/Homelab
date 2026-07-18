# Unifi Object-Oriented Networking (OON) Policies

**Created:** 2026-07-09  
**Last updated:** 2026-07-15

## What is Object-Oriented Networking?

Object-Oriented Networking (OON) is UniFi's policy model where you define reusable **objects** — clients, client groups, networks, zones, regions, apps, IP/port groups — and then write policies that reference those objects instead of raw IP addresses and ports. The UniFi full stack (gateway, switches, APs) works together as one system, so when you apply a policy the controller **automatically generates** the underlying firewall rules, ACLs, routing entries (the policy/route table), and QoS/zone assignments needed to enforce it across every device.

Because the rules are tied to objects rather than static addresses, they update automatically as the network changes — if a device gets a new IP, joins a group, or moves between networks, the relevant firewall rules, ACLs, and routes are re-created for you without manual editing. In short: you describe *intent* against objects, and UniFi handles the low-level rule creation, routing, and zone plumbing behind the scenes.

## OON Policies

| Policy | Enabled | Target Type | Applies To | Action |
|---|---|---|---|---|
| Proton OON | Disabled | Clients | 3 MACs: `REDACTED_MAC_023`, `REDACTED_MAC_001`, `REDACTED_MAC_022` | Route all traffic → ProtonVPN (kill switch on) |
| PC 1 | Disabled | Client | 1 MAC: `REDACTED_MAC_021` | QoS: prioritize all traffic (always) |
| isolate | Disabled | Network | DMZ (VLAN 30) | Route all traffic → ProtonVPN (kill switch on) |
| QoS for D | Enabled | Group | D_devices (5 clients) | QoS: prioritize all traffic (always) |

**Summary:** 4 OON policies — only **QoS for D** is currently active. Two policies (Proton OON, isolate) are VPN policy-based routing rules pointing at the ProtonVPN network with kill switches enabled, but both are disabled.
