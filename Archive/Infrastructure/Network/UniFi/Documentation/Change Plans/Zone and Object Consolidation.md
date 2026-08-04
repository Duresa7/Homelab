# Zone and Object Consolidation

**Created:** 2026-07-27  
**Last updated:** 2026-07-29

**Status:** Completed 2026-07-27

I archived this plan after all nine steps completed. The measured result, plan variance, verification, and rollback map are in [Zone and Object Consolidation - 2026-07-27](../../../../../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Zone%20and%20Object%20Consolidation%20-%202026-07-27.md).

I run 18 routed subnets, 16 firewall zones, and 431 firewall policies for 32 online clients. (19 subnets when I verified on the morning of 2026-07-27; I deleted AD-SERVERS/65 later that day.) 61 of those policies are mine; the controller generates the other 370. This plan cuts the zone count and moves the per-host detail out of policy bodies into reusable objects, so adding a workload stops meaning writing new policies.

## Goal

Separate three things I currently treat as one. A VLAN is a broadcast domain and it's cheap. A zone is a trust posture and it costs me a quadratic default-policy matrix. An object group is a workload identity and it's free.

Once those are split, the rule for new work becomes: pick a zone, add the host to a group. No new VLAN, no new policy.

## Why the policy count is what it is

A V2 policy names exactly one source zone and one destination zone, so the number of policies I hand-maintain works out to the number of service-to-backend relationships multiplied by the zone boundaries they cross. `monitor-01` scrapes hosts in six zones, which is why one collector needs 15 policies. Nginx Proxy Manager reaches six backends across three zones and needs 9.

Neither number describes complexity in my network. Both describe my zone map.

Zones charge me twice. The controller generates one default allow or block per ordered zone pair, so 16 zones sets a floor of 256 such entries before I write a single policy of my own. Generated policies stood at 234 on 2026-07-22 and 370 on 2026-07-27, against 61 of mine. Six generated for every one I maintain.

## Scope

In scope: zone consolidation for the observability and cluster segments, reusable address and port groups, the two misspelled zone names, the `Secure-V` VLAN, client-group cleanup, and the configuration records that describe all of it.

Out of scope, deliberately: the Kasm lab. `KASM-BROWSER`/74, `MALWARE-OFFLINE`/77, and `EVIDENCE-QUARANTINE`/79 keep their three separate zones, their ten policies, and their `KASM Lab Proton Egress` traffic route. Those three zones can't reach each other, and that non-adjacency is the point of the design. I'm building session isolation separately, so nothing here touches them.

Also out of scope: merging `AlphaSec-Access` into the observability zone. Its egress posture matches, but `docker-network` at `192.168.85.2` fronts internet traffic through Nginx Proxy Manager. Putting it in the same zone as Splunk and Grafana would hand a compromised proxy intra-zone reach into the SIEM. That boundary earns its keep, so Access-A stays on its own zone.

## Verified starting state

I read this from the controller on 2026-07-27, not from these records. Zone membership isn't available from the zone endpoint; see [UniFi zone membership is absent from the zone-matrix endpoint](../../../../../../Infrastructure/Network/UniFi/Documentation/Troubleshooting/UniFi%20Zone%20Membership%20Absent%20From%20Zone-Matrix%20Endpoint%20-%202026-07-27.md) for why, and for the read that does work.

| Zone | Networks (verified by `firewall_zone_id`) |
|---|---|
| Internal | Management, Trusted/10, Personal-A/40, Secure/50, Secure Client/60 (AD-SERVERS/65 was a member; deleted later on 2026-07-27) |
| Untrusted | IoT/20, **Secure-V/100** |
| Dmz | DMZ/30, DMZ-A/90 |
| `AlphaSec-Servers` | SERVERS-A/80 |
| `AlphaSec-Mgmt` | MGMT-A/70 |
| `AlphaSec-Security` | Security-A/72 |
| `AlphaSec-Monitor` | MONITOR-A/73 |
| `AlphaSec-Access` | Access-A/85 |
| `AlphaSec-Cluster` | Cluster-Net/71 |
| KASM-BROWSER | KASM-BROWSER/74 |
| MALWARE-OFFLINE | MALWARE-OFFLINE/77 |
| EVIDENCE-QUARANTINE | EVIDENCE-QUARANTINE/79 |

Eleven of those twelve rows matched what I had already written down. The exception is `Secure-V`/100, which sits in the built-in `Untrusted` zone and appeared in none of my records.

Zero IPv4 address groups exist. Five port groups exist. Every policy that targets a host spells the address inline.

## Tooling constraint that sets the sequence

The UniFi Network MCP can't do half of this, and that decides what runs as an automated step versus a controller-UI step. I confirmed each row below against the plugin's models and its live tool surface.

| Operation | MCP support |
|---|---|
| Create, update, delete address and port groups | Yes |
| Create, update, delete firewall policies | Yes |
| Reference a group from a policy (`ip_group_id`, `port_group_id`) | Yes |
| Create, update, delete client groups | Yes |
| Read which networks are in a zone | No; read `firewall_zone_id` per network instead |
| Rename a zone | No, UI only |
| Create or delete a zone | No, UI only |
| Move a network between zones | No, UI only |
| Delete a network | No, UI only; `enabled: false` works from the MCP |

So every zone change in this plan happens in the controller UI by hand, and every object and policy change can be scripted. I take a firewall snapshot before each UI step because I can't roll one back with a tool call.

Two known plugin behaviours apply while editing policies. A policy update silently drops `description` rather than failing, so I read every policy back after writing it. Enabling `create_allow_respond` after creation does not retroactively create the return rule, which I hit on 2026-07-12; if a path needs a return companion I confirm the companion exists rather than trusting the flag.

## Target zone set

Custom zones drop from 9 to 6, and the total from 16 to 13.

| Zone | Posture | Networks after this plan |
|---|---|---|
| `AlphaSec-Mgmt` | Hypervisor plane | MGMT-A/70, Cluster-Net/71 |
| `AlphaSec-Servers` | Internal app and data | SERVERS-A/80 |
| `AlphaSec-Observability` | Security, detection, monitoring | Security-A/72, MONITOR-A/73 |
| `AlphaSec-Access` | Ingress hinge | Access-A/85 |
| KASM-BROWSER, MALWARE-OFFLINE, EVIDENCE-QUARANTINE | Lab, untouched | 74, 77, 79 |

13 zones is 169 ordered pairs against today's 256, a third fewer pair-defaults for the controller to generate. I'll record the actual generated count before and after rather than predicting it, since the generated set also holds return companions, invalid-state drops, and gateway-service entries that don't scale with the zone matrix.

## Steps

### S01: Snapshot and reference inventory

I export the full firewall policy set, the zone list, the network list with each `firewall_zone_id`, the firewall groups, and the client groups to `Evidence/Zone and Object Consolidation - YYYY-MM-DD/Exports/`. This is the rollback baseline for every later step.

I also inventory which client groups any policy or OON policy actually references. I'm not deleting a group on the assumption that nothing uses it.

Stop condition: if the policy count read back doesn't match 61 custom entries, I stop and reconcile before touching anything.

### S02: Create the address and port groups

This step is pure addition. Nothing references the groups yet, so it can't break a path.

| Group | Type | Members | Policies it de-duplicates |
|---|---|---|---|
| `OBJ-Monitor-Collector` | address-group | 192.168.73.2 | 15 |
| `OBJ-Reverse-Proxy` | address-group | 192.168.85.2 | 9 |
| `OBJ-Security-Stack` | address-group | 192.168.72.2, 192.168.72.3 | 7 |
| `OBJ-Proxmox-Nodes` | address-group | 192.168.70.10 through .13 | 2 |
| `OBJ-Observability-Hosts` | address-group | 192.168.72.2, .3, 192.168.73.2 | new, used in S06 |
| `PG-Node-Exporter` | port-group | 9100, 9101 | 4 exact, 6 contain 9100 |
| `PG-Egress-Web` | port-group | 80, 443 | 3 |
| `PG-NTP` | port-group | 123 | 3 |

`group_type` can't be changed after creation, so I set it correctly the first time.

### S03: Repoint policies onto the groups

I rewrite each policy's source or destination from `matching_target_type: SPECIFIC` with inline `ips` to `OBJECT` with the group ID, in batches by group, verifying after each batch. `monitor-01` first, because 15 policies carry that one address and it's the change with the most leverage.

The win is maintenance, not behaviour. Moving `monitor-01` today means 15 policy edits. After this step it's one group edit.

Check after each batch: the policy reads back with the group reference, the description survived, and the monitored path still works. Prometheus target health is the fastest signal that a scrape path broke.

Rollback: restore the inline `ips` from the S01 export for that policy.

### S04: Fix the two zone names

Four custom zones spell the organisation prefix in full. Two spell it one character short. I correct those two in the controller UI so all six match.

This is cosmetic and carries no traffic risk. It's in the plan because these records render the prefix as `AlphaSec`, which hid the typo from every review I've done. Worth knowing that the scrub placeholder can mask a real controller defect.

### S05: Merge Cluster-Net into the Mgmt zone

I do this before the observability merge because no custom policy references `AlphaSec-Cluster`. Zero. That makes it the safe rehearsal for the UI procedure I need in S06.

In the UI I move Cluster-Net/71 into `AlphaSec-Mgmt`, then delete the emptied `AlphaSec-Cluster` zone. Corosync link1 is intra-VLAN traffic that never reaches the gateway, so there's no routed dependency to break.

Two settings to preserve: Cluster-Net has `dhcpd_enabled: false` and `internet_access_enabled: false`. I verify both survived the move.

Behaviour change to accept: MGMT-A/70 and Cluster-Net/71 land in one zone, so UniFi's intra-zone default allows traffic between them. Nothing needs that path today. The Proxmox Datacenter firewall enforces independently either way.

Check: `pvecm status` shows four nodes, quorum intact, both links active. GUI and SSH on 192.168.70.10 through .13 still answer.

Stop condition: if the controller refuses to delete the zone, I leave it empty and move on rather than forcing it. An empty zone costs generated policies, not correctness.

### S06: Merge Security-A and MONITOR-A into one observability zone

This is the risky step. Postures already match: inbound from Internal and VPN, egress default-deny except web and NTP, and Prometheus already scrapes both sides while Wazuh agents ship into them.

I keep `AlphaSec-Monitor` as the surviving zone because 15 policies reference it against 10 for `AlphaSec-Security`, then rename it to `AlphaSec-Observability`. Repointing 9 policies beats repointing 15.

Order matters, and it's the opposite of what feels natural:

1. Repoint the 9 `AlphaSec-Security`-only policies to the surviving zone.
2. Move Security-A/72 into the surviving zone in the UI.
3. Delete `Allow Monitor to A-Security monitoring`. Once both networks share a zone that scrape is intra-zone, and the intra-zone default already permits it.
4. Delete the emptied `AlphaSec-Security` zone.
5. Rename the survivor to `AlphaSec-Observability`.

Policies must be repointed before the network moves. A policy that still names the old zone after its network has left silently stops matching, and one of those policies is `Block AlphaSec-Security Other External Egress`. A BLOCK that stops matching is a hole, not an outage, so it won't announce itself.

The egress index collision is the part that needs designing rather than discovering. Policy index order is scoped per zone pair. After the merge, Security-A's trio and MONITOR-A's pair share the (Observability to External) pair, and both start at index 10000:

- `Allow Security Workloads Web Egress` at 10000 against `Allow Monitor Web Egress` at 10000
- `Allow Security Workloads NTP Egress` at 10001 against `Allow Monitor NTP Egress` at 10001

I collapse all five into three, sourced from `OBJ-Observability-Hosts`: web at 10000, NTP at 10001, terminal block at 10002. Five policies become three and the collision disappears.

Checks, all of which have to pass before I delete anything: every Prometheus target still reports `UP`; the Wazuh manager on 192.168.72.2 still accepts agent traffic on its port group; NPM still reaches the Wazuh dashboard, Splunk Web, Grafana, PeaNUT, and Prometheus; Jedi PC's break-glass path to 192.168.73.2 still answers on 3000, 8090, and 9090; `ansible-01` still reaches SSH on 192.168.73.2; and the two SIEM hosts still resolve DNS and reach NTP while everything else outbound is denied.

Rollback: recreate the deleted zone, move Security-A back, restore the 10 policies from S01. Recreating a zone is a UI operation, so I don't start this step without the export in hand.

### S07: Remove Secure-V

The decision gate this step originally carried is resolved. When I first mapped `Secure-V`/100 it was a working domain wireless network: an enabled SSID, a ProtonVPN traffic route, and a Windows Group Policy WLAN profile naming that SSID as the only one domain machines may join. I decided on 2026-07-27 to retire the whole Windows domain, which dissolves the GPO dependency, and I deleted the `Kadi-AP-AD` SSID the same day. The domain-side teardown lives in the archived [Active Directory Decommission plan](../../../../../Platforms/Windows%20Servers/Documentation/Change%20Plans/Active%20Directory%20Decommission.md).

What remains here is two objects, in this order:

1. Delete the `Non-tracking` traffic route (route ID `6a5c5b960e10fae12278c5d6`). It's enabled with a kill switch and targets this network; removing the network first would leave a route pointing at nothing.
2. Delete the `Secure-V` network (`6a5c5b620e10fae12278c51d`) in the controller UI. The MCP can toggle a route but can't delete a network.

The Proxmox-Trunk port profile needs no edit. It stores an exclusion list rather than a tagged list, and `Secure-V` is one of its six exclusions; the controller drops the entry when the network goes, the same way it dropped AD-SERVERS/65 automatically.

Check: the network list returns 25 entries, no WLAN references VLAN 100, the traffic-route list holds two routes, and the trunk's exclusion list holds five entries.

Separately, `AlphaSec-IoT` is a disabled SSID bound to the untagged Management network. It's off, so nothing is on the management LAN because of it, but that isn't where an IoT SSID should point even while disabled. Rebind or delete it while in the WLAN screen.

### S08: Client group hygiene

14 client groups exist and most are referenced by nothing. `QoS for D` is the only enabled OON policy and it targets `D_devices`, so that group is load-bearing and I leave it alone.

- `IOT` has zero members and `iot_device` has six. I delete the empty one and keep the populated one.
- `server` holds one MAC, `docker-blue`. I rename it to what it is.
- `grey-server` holds five MACs: `grey-node` itself plus four VM addresses. The name says node, the contents say node plus guests. I decide which it's meant to be and rename accordingly.
- `VM` holds `wazuh-01` and `kasm-01`, two unrelated hosts under a name that describes neither. Because it contains a Kasm host I flag it rather than change it in this plan.
- `Game Servers` holds one MAC that isn't in the current online set. I confirm whether the host still exists before deciding.
- `Admin_Device` already contains exactly the four approved administrative devices, while `Device Access to Proxmox` still matches four MACs inline.

That last one looks like an obvious consolidation and I'm not planning it yet. The V2 policy schema's `matching_target` enum is `ANY`, `IP`, `NETWORK`, and `OBJECT`, with no client-group selector, so I need to confirm in the UI how a MAC-matched policy is actually stored before claiming a client group can replace it.

Every deletion in this step waits on the S01 reference inventory.

### S09: Update the records

The configuration records are the deliverable, not a follow-up. Networks and VLANs, zones, firewall policies, and objects each get the post-change state, and the dated account goes to `Documentation/Change Records/`.

Six corrections were true of the records regardless of whether any step above runs, so I applied them on 2026-07-27 when I verified the starting state:

- Added `Secure-V`/100 to the networks table with its SSID, GPO, and Proton-route context, and to the `Untrusted` row of the zone membership table
- Replaced the stale "39 user-defined" figure with the measured 431 total against 61 of mine, and dated the per-category generated breakdown to its 2026-07-22 snapshot
- Corrected the claim that VLAN 74 is empty, and recorded the unidentified host at 192.168.74.49
- Added the missing traffic-route inventory to the objects record
- Recorded the address-group gap and the inline-address reuse counts in the firewall record
- Recorded the zone-name mismatch and the placeholder that hid it

## Open items this plan doesn't resolve

An unnamed Proxmox VM at `<YOUR_UNNAMED_LAB_VM_MAC>` has been online on KASM-BROWSER/74 since 2026-07-23. Its address, 192.168.74.49, sits outside the .100 through .199 DHCP pool and it has no fixed-IP reservation, so something is configuring that address by hand. Identifying it is Kasm work and stays with the Kasm effort; I'm recording it here only because it contradicts what my records claim about VLAN 74.

## Risks

The observability merge is the only step that can silently reduce enforcement, because a BLOCK policy pointing at a zone its network has left stops matching without erroring. Repointing before moving is what prevents it, and the egress check after S06 is what proves it.

The zone operations have no tool-level rollback. Recreating a deleted zone and rebuilding its policies is manual work against the S01 export, which is why the export happens first and why S05 rehearses the procedure on a zone that no policy references.

Nothing in this plan is a substitute for a Proxmox-side check. A UniFi policy is never sufficient on its own for traffic landing on a node; the Datacenter firewall enforces independently, which the NUT path proved on 2026-07-25. I test from the source host after each step rather than assuming the gateway is the only gate.
