# UniFi Kasm Firewall Audit

**Created:** 2026-07-22  
**Last updated:** 2026-07-27

> Superseded as a description of live state. This is the retained 2026-07-22 baseline of the original seven-VLAN Kasm build. On 2026-07-23 I cut the lab to three VLANs (74, 77, 79) and nine firewall policies, deleted VLANs 73, 75, 76, and 78 with their zones, removed the `MALWARE-ONLINE` zone entirely, and retargeted the Proton route to VLAN 74 alone. The numbers below describe the configuration as measured on 2026-07-22 and are kept as the first retained score, not as current fact. See the [Kasm lab network simplification](../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Kasm%20Lab%20Network%20Simplification%20-%202026-07-23.md) and the [Kasm Workspaces deployment](../../Platforms/Kasm%20Workspaces/Documentation/Deployment.md).

## Scope and Result

I audited the UniFi firewall after creating the Kasm zones, policies, Proton route, and Proxmox trunk membership. The deterministic auditor scored the controller 46/100 and rated it critical. The score is useful as a strict configuration baseline, but it does not mean the Kasm zones have an observed open route. Most deductions come from the rubric requiring one explicit user policy for every ordered VLAN pair even when both custom zones default to `Block All`.

I did not enable a lab client or run malware during this assessment.

## State Reviewed

| Item | Observed state |
| --- | --- |
| UniFi Network | 10.4.57 |
| Adopted devices | 5 online; no stable updates pending |
| Networks and zones | 30 networks; 19 zones |
| User firewall policies | 91 total; 52 named for Kasm |
| Kasm policy state | 48 enabled; 4 intentionally disabled Gateway DNS allows |
| Kasm Proton route | Enabled for VLANs 73, 74, 75, and 78 with kill switch |
| Proxmox trunk | All seven lab VLANs present in the custom tagged set |
| Audit score | 46/100, first retained baseline |

## Score Breakdown

| Domain | Score | Findings | Interpretation |
| --- | ---: | ---: | --- |
| Segmentation | 0/25 | 387 | One existing MGMT-A exposure plus 386 explicit-rule completeness findings |
| Egress | 20/25 | 3 | Existing IoT egress, resolver enforcement, and threat-intelligence gaps |
| Hygiene | 4/25 | 18 | Existing descriptions and shadowed-policy debt |
| Topology | 22/25 | 3 | Three existing port profiles have no explicit switch-port reference |

## Material Finding

The existing Internal-to-management and VPN-to-management policies permitted broad paths into MGMT-A. That did not come from the Kasm change, but it conflicted with the benchmark's admin-only management requirement. I completed the correction in [MGMT-A Final Lockdown - 2026-07-27](../../Infrastructure/Network/UniFi/Documentation/Change%20Records/MGMT-A%20Final%20Lockdown%20-%202026-07-27.md).

## Kasm Interpretation

The auditor emitted 386 `SEG-04` findings because it expects an explicit user rule for every ordered VLAN pair. UniFi's custom-zone default for the seven Kasm zones is `Block All`, and the Kasm workflow exceptions are explicit. I did not create hundreds of duplicate block rules because they would increase policy-order risk without changing the zone default.

The Kasm egress design advertises Quad9 to the Proton-routed VLANs and blocks their Gateway DNS path. It does not yet intercept or reject every attempt to use a different public resolver on port 53. That remains an acceptance-test and hardening item. `MALWARE-ONLINE` allows DNS, NTP, HTTP, and HTTPS before its final External block; the offline, target, and evidence zones have explicit External blocks.

## Other Existing Findings

- IoT has no explicit External egress filter.
- No threat-intelligence IP group is configured.
- Fifteen older policies have no description. Every Kasm policy has a description.
- A broad Internal-to-management allow shadows two narrower policies, and one duplicate DMZ block shadows another.
- The Management, Trusted, and IoT custom port profiles have no explicit switch-port reference in the gathered topology.

## Required Verification

I will use harmless clients to test each Kasm VLAN before I deploy a malware-capable template. The tests must prove blocked management, cluster, server, trusted, and direct-WAN paths; allowed attacker-to-target and Kasm control paths; target and evidence initiation blocks; approved DNS behavior; Proton public IP; and loss of Internet access when the Proton client is disabled.

## Closure

The audit is complete as the first retained controller baseline. The Kasm network boundary remains unaccepted until packet-flow tests pass. The pre-existing MGMT-A exposure remains open under its existing segmentation project.
