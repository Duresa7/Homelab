# Zone and Object Consolidation Evidence Index

**Created:** 2026-07-27  
**Last updated:** 2026-08-04

I keep the unsanitized controller exports for this change local-only. The public evidence set contains the reviewed step logs and this index, while controller exports containing client MAC addresses and other unreviewed controller state remain unpublished. S02 through S08 retain before-and-after state, but the step logs identify the original mutation or UI transcripts that weren't retained.

| Step | Evidence | Observed result |
|---|---|---|
| S01 | [Snapshot transcript](Logs/S01-Snapshot-and-Reference-Inventory.md) | The controller returned 431 policies: 61 custom & 370 predefined. The plan's stop condition passed. |
| S01 | `Exports/S01-Firewall-Policies.json` | Full 431-policy rollback baseline, including rule bodies, order indexes, zone IDs, and enabled state |
| S01 | `Exports/S01-Firewall-Zones.json` | All 16 zones & their controller IDs |
| S01 | `Exports/S01-Networks-With-Zone-IDs.json` | All 26 networks plus one full detail read per network, including `firewall_zone_id` |
| S01 | `Exports/S01-Firewall-Groups.json` | Five pre-change port groups & zero pre-change IPv4 address groups |
| S01 | `Exports/S01-Client-Groups.json` | All 14 client groups & their exact members |
| S01 | `Exports/S01-OON-Policies.json` | All four OON policies & their targets |
| S01 | `Exports/S01-Client-Group-Reference-Inventory.json` | Only `D_devices` is referenced; enabled OON policy `QoS for D` targets it |
| S02 | [Firewall group creation](Logs/S02-Firewall-Group-Creation.md) | Five address groups & three port groups were added one at a time; policies stayed at 61 and zones at 16 |
| S02 | `Exports/S02.1-Before-OBJ-Monitor-Collector-Firewall-Snapshot.json` through `Exports/S02.8-After-Firewall-Snapshot.json` | Full before, inter-step, and final policy-zone-group rollback state for every create |
| S03 | [Policy selector migration](Logs/S03-Policy-Selector-Migration.md) | 35 exact selectors across 24 policies now use groups; 11 partial or excluded selectors stayed inline to prevent behavior drift |
| S03 | `Exports/S03-Policy-Selector-Migration-Ledger.json` | Exact before and after selectors, controller IDs, skipped selectors, & zero invariant-field errors |
| S03 | `Exports/S03.1-Before-Allow-Automation-to-monitor-01-SSH-Firewall-Snapshot.json` through `Exports/S03.35-After-Final-Firewall-Snapshot.json` | Full rollback and structural-diff state around each policy mutation |
| S04 | [Zone name corrections](Logs/S04-Zone-Name-Corrections.md) | Both shortened names were corrected in the UI and read back through the controller API |
| S04 | `Exports/S04.1-Before-Rename-AlphSec-Servers-Firewall-Snapshot.json` through `Exports/S04.2-After-Zone-Renames-Firewall-Snapshot.json` | Full before, inter-step, and final snapshots; each diff changed one zone name and nothing else |
| S05 | [Cluster-Net zone merge](Logs/S05-Cluster-Net-Zone-Merge.md) | VLAN 71 moved into `AlphaSec-Mgmt`, the empty zone was removed, and all Proxmox checks passed |
| S05 | `Exports/S05.1-Before-Move-Cluster-Net-Firewall-Snapshot.json` through `Exports/S05.2-After-Cluster-Net-Merge-Firewall-Snapshot.json` | Full rollback state around the network move and zone deletion |
| S06 | [Observability zone merge](Logs/S06-Observability-Zone-Merge.md) | Security-A and MONITOR-A now share `AlphaSec-Observability`; the final service gate passed |
| S06 | `Exports/S06-Security-Zone-Policy-Repoint-Ledger.json` | Exact previews and readbacks for all nine zone-reference updates |
| S06 | `Exports/S06.1-Before-Allow-Internal-to-AlphaSec-Security-Firewall-Snapshot.json` through `Exports/S06.19-After-Final-Observability-Egress-Collapse-Firewall-Snapshot.json` | Full structural state before and after every policy, network, zone, and ordering mutation |
| S06 | `Exports/S06-Service-Gate-Before-Egress-Policy-Deletions.json` | All required service paths passed before either redundant egress allow was removed |
| S06 | `Exports/S06-Final-Service-Gate.json` | All required service paths passed after the final three-policy order was restored |
| S07 | [Secure-V removal](Logs/S07-Secure-V-Removal.md) | The route and network were removed in dependency order, and the disabled IoT WLAN now points to VLAN 20 |
| S07 | `Exports/S07.1-Before-Delete-Non-Tracking-Route-Snapshot.json` through `Exports/S07.4-Final-Secure-V-Removal-Snapshot.json` | Full route, network, WLAN, trunk-profile, and firewall state around each S07 mutation |
| S08 | [Client group hygiene](Logs/S08-Client-Group-Hygiene.md) | Two groups were renamed, two unreferenced obsolete groups were removed, and `D_devices` stayed attached to `QoS for D` |
| S08 | `Exports/S08.1-Before-Client-Group-Hygiene-Snapshot.json` and `Exports/S08.2-After-Client-Group-Hygiene-Snapshot.json` | Full before-and-after client-group state, dependency checks, host identity checks, and final reference verification |
| S09 | [Final verification](Logs/S09-Final-Verification.md) | The final controller counts, zone membership, service paths, documentation, and archive state were reconciled |
| S09 | `Exports/S09-Final-Controller-State.json` | Final measured counts, zone membership, preserved settings, deleted-object absence, and policy delta |

S01 completed before the Active Directory decommission changed UniFi, Proxmox, Ansible, Termix, or `<REDACTED_PASSWORD_MANAGER>`. S02 began after that plan finished.
