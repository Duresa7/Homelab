# UniFi Firewall Audit

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

## Scope and Result

I ran a read-only audit after the zone and object consolidation finished. I checked controller health, every current firewall policy, zone membership, network objects, WLANs, traffic routes, switches, switch ports, and port profiles.

The deterministic UniFi firewall auditor scored the current controller 62/100 and rated it `needs_attention`. This is an independent hardening score, not a failure of the consolidation verification. The consolidation counts, zone memberships, service gates, and named invariants remained correct.

## State Reviewed

| Item | Observed state |
| --- | --- |
| UniFi Network | 10.4.57 |
| Controller | Ahsoka Gateway |
| Service health | WAN, internet, LAN, WLAN, and VPN reported healthy |
| Adopted devices | Five online; no upgrade or end-of-life flag |
| Active alarms | None |
| Networks and zones | 25 network objects; 14 zones |
| Firewall policies | 361 total; 59 custom; 302 controller-generated |
| Firewall groups | 13 |
| WLANs | Four; three enabled and one disabled |
| Traffic routes | Two; one enabled and one disabled |
| Switches | Three online |
| Switch port profiles | Four custom profiles |

## Score

| Domain | Score | Findings |
| --- | ---: | ---: |
| Segmentation | 20/25 | 1 |
| Egress control | 20/25 | 3 |
| Rule hygiene | 0/25 | 31 |
| Topology | 22/25 | 3 |
| Overall | 62/100 | 38 |

The [scoring output](../Evidence/UniFi%20Firewall%20Audit%20-%202026-07-27/Logs/Firewall-Audit-Score.json) records rubric version 1 and the exact category deductions.

## Material Findings

| Benchmark | Severity | Finding |
| --- | --- | --- |
| SEG-03 | Critical | The base Management network remains in `Internal`. The controller-generated Internal allow therefore permits access from other Internal networks instead of limiting management access to named administrative sources. |
| HYG-02 | Critical | `Allow VPN to `AlphaSec-Servers`` precedes the Temp VPN block. It would shadow that block if Temp VPN were enabled. Temp VPN is currently disabled, so this is a latent conflict rather than a current active path. |
| EGR-01 | Warning | IoT traffic in `Untrusted` retains default External access without an effective restrictive terminal egress policy. |
| EGR-02 | Warning | The API result does not prove DNS interception or forced resolver use. The signed-in controller tab was present, but the read-only browser connection timed out before the settings page could be inspected. I made no repeated sign-in request. |
| HYG-05 | Warning | `Block DMZ to LAN` is shadowed by the preceding equivalent `Block DMZ to Internal` policy. |

## Informational Findings

- No threat-intelligence or malicious-destination group is applied to an active policy.
- Twenty-nine custom policies have an empty description.
- The custom `Management`, `Trusted`, and `IoT` switch port profiles have no current port reference. `Proxmox-Trunk` is referenced.

## Checks That Passed

- `Untrusted` has an explicit controller-generated block toward `Internal`.
- No Guest network or Guest WLAN exists, so the Guest isolation benchmark does not apply.
- Every zone pair has a controller-generated default policy.
- Every referenced firewall group exists and contains a member.
- Current policy names identify their intended action or path.
- Every switch uplink and trunk carried the expected tagged networks.
- No significant switch-port error condition was present in the current counters.
- The controller reported no active alarm.

## Evidence Boundary

I retained the deterministic score output. The controller and switch reads were live MCP queries, but I did not retain their raw API payloads as files. This assessment records the observed counts, benchmark results, and UI timeout without reconstructing a transcript after the fact.

## Remaining Work

I did not change live firewall or switch configuration during this review. A separate approved hardening change should:

1. limit the base Management network to named administrative sources;
2. place the Temp VPN block before any broader VPN allow, or narrow the broader allow;
3. define the intended IoT egress and DNS-enforcement model;
4. remove the redundant DMZ block;
5. add descriptions to the 29 undocumented custom policies; and
6. remove the three unused port profiles after confirming they are not kept as manual templates.

