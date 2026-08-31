# DMZ-A VLAN 90 Removal

**Created:** 2026-08-29  
**Last updated:** 2026-08-31

## Date

I completed this change on 2026-08-29.

## Scope

I deleted `DMZ-A` (VLAN 90, `192.168.90.0/24`) from the Ahsoka Gateway. This closes the open item left by [edge-01 Move to DMZ VLAN 30](edge-01%20Move%20to%20DMZ%20VLAN%2030%20-%202026-08-07.md), which moved my only DMZ-A workload to DMZ (VLAN 30) on 2026-08-07 and kept the empty VLAN through a soak period.

I did not touch DMZ (VLAN 30), the `Dmz` firewall zone, `edge-01`, or any port profile. The soak period ran 22 days.

## Why the VLAN existed and why it is gone

I created DMZ-A because `Proxmox-Trunk` did not carry VLAN 30, so I could not put a virtualised workload on the original DMZ. On 2026-08-07 I removed DMZ from the trunk's exclusion list, which removed the reason for a second DMZ. One DMZ now carries the edge host, and two DMZs splitting the role was the only thing DMZ-A was doing.

## Pre-removal dependency check

I checked every place a network object can be referenced before deleting anything. All five came back clean.

| Check | Tool | Result |
|---|---|---|
| Clients on the subnet | `unifi_list_clients`, `include_offline: true` | 0 of 0, online and offline |
| Firewall policies | `unifi_list_firewall_policies`, all 65 user-defined | No policy names network `698cc13a10cb5676c296c637` in a source or destination |
| Static routes | `unifi_list_routes` | 0 routes defined on the site |
| Port forwards | `unifi_list_port_forwards` | 0 rules defined on the site |
| Port profiles | `unifi_list_port_profiles` | Not named in any of the 5 profiles |

The port-profile result needs one word of explanation, because "not named" reads like the wrong answer. `Proxmox-Trunk` and `Server-Provision` are `customize`/`custom` profiles that work by exclusion: they carry every network *except* the ones in `excluded_networkconf_ids`. DMZ-A was in neither exclusion list, so the trunk was carrying it, and deleting the network is what takes it off the trunk. There was nothing to unpin first.

The delete preview also confirmed `firewall_zone_id` was the built-in `Dmz` zone, which DMZ (VLAN 30) shares. Removing DMZ-A therefore leaves the zone and `edge-01`'s zone membership intact.

## What I changed

One delete, through the plugin's preview-then-confirm flow:

```text
unifi_delete_network  network_id=698cc13a10cb5676c296c637   → preview
unifi_delete_network  network_id=698cc13a10cb5676c296c637  confirm=true
→ "Network 'DMZ-A' deleted successfully."
```

## Verification

**The controller now reports 22 network objects, down from 23.** `unifi_list_networks` returns no object with VLAN 90 or subnet `192.168.90.0/24`. The Networks table in the UI shows 15 routed LANs, with DMZ (30) present and DMZ-A absent.

**The honeypot at `192.168.90.2` is gone with it.** This was the part of the open item I could not confirm from the records, because no inventory ever listed a honeypot guest. It was not a VM: it is the gateway's built-in honeypot, configured per network under CyberSecure. The honeypot table now reads:

| Network | Subnet | Honeypot address |
|---|---|---|
| Management | 192.168.1.0/24 | 192.168.1.2 |
| DMZ | 192.168.30.0/24 | 192.168.30.2 |
| IoT | 192.168.20.0/24 | 192.168.20.2 |

Three entries, none on `192.168.90.0/24`. Deleting the network took its honeypot with it, and no manual cleanup was needed.

Captures are in [Evidence](../../Evidence/DMZ-A%20VLAN%2090%20Removal%20-%202026-08-29/): the Networks table before and after, and the CyberSecure page showing the honeypot table.

## What I found while verifying, and did not change

The CyberSecure capture shows Threat Management inspecting six networks: Trusted, IoT, Personal-A, Secure, Secure Client, and MGMT-A. **DMZ (30) is not among them**, so `edge-01`, the one host reachable from the Internet, passes no IPS inspection. Neither do Security-A, SERVERS-A, Access-A, or MONITOR-A.

The edge-01 record already flagged this on 2026-08-07. Adding networks to Threat Management costs gateway throughput on every added network, so it is a decision on its own rather than a step in a VLAN deletion. I left the list as it was.

**Closed the next day.** I added DMZ to the list on 2026-08-30, which is [DMZ Added to Threat Management](DMZ%20Added%20to%20Threat%20Management%20-%202026-08-30.md). Detection Mode stayed on Notify, so `edge-01` is inspected but nothing is dropped. The tables above and the S03 capture describe 2026-08-29 and are left as they were.

## Record updates

- [network-vlan.md](../../Configuration/network-vlan.md): removed the DMZ-A rows from the VLAN table and the placement table, and corrected the counts to 15 routed LANs of 22 objects.
- [zone.md](../../Configuration/zone.md): the `Dmz` zone row now lists DMZ (VLAN 30) alone.
- [UniFi-Network.md](../../../../../Guides/UniFi-Network.md): corrected the object and LAN counts, and the DMZ's VLAN, which the guide still gave as 90.
- [edge-01 Move to DMZ VLAN 30](edge-01%20Move%20to%20DMZ%20VLAN%2030%20-%202026-08-07.md): marked its open item closed and pointed it here.

Dated records and troubleshooting entries that mention VLAN 90 keep those mentions. They describe what was true when they were written.
