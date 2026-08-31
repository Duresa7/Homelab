# DMZ Added to Threat Management

**Created:** 2026-08-31  
**Last updated:** 2026-08-31

## Date

I made this change on 2026-08-30 and verified it the same day at 11:36 AM.

## Scope

I added DMZ (VLAN 30) to the Selected Networks list under CyberSecure, Threat Management, on the Ahsoka Gateway. `edge-01` at `192.168.30.10` is the only host in this environment reachable from the Internet, and until this change its traffic passed no IPS inspection.

This closes a finding that had been open in two records since 2026-08-07: [edge-01 Move to DMZ VLAN 30](edge-01%20Move%20to%20DMZ%20VLAN%2030%20-%202026-08-07.md) raised it, and [DMZ-A VLAN 90 Removal](DMZ-A%20VLAN%2090%20Removal%20-%202026-08-29.md) confirmed it was still true.

I changed nothing else on the page. Detection Mode, the Active Detections categories, Region Blocking and the honeypot list are as they were.

## What changed

Selected Networks went from six entries to seven:

| Before | After |
|---|---|
| Trusted, IoT, Personal-A, Secure, Secure Client, MGMT-A | Trusted, IoT, Personal-A, Secure, Secure Client, MGMT-A, DMZ |

## Verification

The Threat Management page at 11:36 AM on 2026-08-30 reads:

| Setting | Value |
|---|---|
| Overall Protection Level | Standard (Free) |
| Intrusion Prevention | On |
| Total Signatures | 32,918, updated 2026-08-30 at 4:35 AM via UniFi OS Update |
| Selected Networks | Trusted, IoT, Personal-A, Secure, Secure Client, MGMT-A, DMZ |
| Detection Mode | Notify |

Active Detections are Botnets and Threat Intelligence 5 of 5, Viruses, Malware and Spyware 4 of 4, Hacking and Exploits 5 of 5, Peer to Peer and Dark Web 3 of 3, Attacks and Reconnaissance 6 of 6, and Protocol Vulnerabilities 11 of 12.

The UniFi Network MCP does not expose the Threat Management network list. `unifi_tool_index` returns only `unifi_get_ips_events` and `unifi_get_gateway_settings` for this area, and neither carries the Selected Networks field, so the page capture is the record of state rather than an API read. The capture is in [Evidence](../../Evidence/DMZ%20Added%20to%20Threat%20Management%20-%202026-08-30/).

## Detection Mode is Notify, not Notify and Block

This is worth stating plainly, because "DMZ is now inspected" invites the wrong conclusion. Notify means the gateway raises an alert on a signature match and forwards the packet anyway. Nothing is dropped. The change buys visibility on the edge host, not enforcement on it.

I left it on Notify on purpose. Switching to Notify and Block turns a false positive into an outage on the one path that serves traffic from outside, and I would rather see what the signatures actually match on this network for a while before I let them drop anything.

I changed that on 2026-08-31, and Detection Mode is now Notify and Block. This section stays as written because it describes the 2026-08-30 capture and the reasoning that held then. [Detection Mode to Notify and Block](Detection%20Mode%20to%20Notify%20and%20Block%20-%202026-08-31.md) records the switch, including the fact that it went ahead without the run of signature matches this section asked for.

## What is still uninspected

Eight of the fifteen routed LANs remain outside Threat Management:

| Network | VLAN | Subnet |
|---|---:|---|
| Management | none | 192.168.1.0/24 |
| Server-Provision | 5 | 192.168.5.0/24 |
| Proton-WiFi | 45 | 192.168.45.0/24 |
| Cluster-Net | 71 | 192.168.71.0/24 |
| Security-A | 72 | 192.168.72.0/24 |
| MONITOR-A | 73 | 192.168.73.0/24 |
| SERVERS-A | 80 | 192.168.80.0/24 |
| Access-A | 85 | 192.168.85.0/24 |

Cluster-Net carries Corosync and nothing else, so inspecting it adds latency to the one traffic class that is least tolerant of it. The rest are a throughput decision on their own, since every added network costs gateway processing.

## Record updates

- [edge-01 Move to DMZ VLAN 30](edge-01%20Move%20to%20DMZ%20VLAN%2030%20-%202026-08-07.md) marks its Threat Management item closed and points here.
- [DMZ-A VLAN 90 Removal](DMZ-A%20VLAN%2090%20Removal%20-%202026-08-29.md) keeps its finding as written, because it describes what the 2026-08-29 capture showed, with a line saying it was closed the next day.

## Remaining work

- Detection Mode moved to Notify and Block on 2026-08-31, before any signature match had been recorded. It is one gateway-wide control, so enforcement covers all seven inspected networks and not DMZ alone. [Detection Mode to Notify and Block](Detection%20Mode%20to%20Notify%20and%20Block%20-%202026-08-31.md).
- Decide whether SERVERS-A, Security-A, MONITOR-A and Access-A are worth the gateway throughput.
