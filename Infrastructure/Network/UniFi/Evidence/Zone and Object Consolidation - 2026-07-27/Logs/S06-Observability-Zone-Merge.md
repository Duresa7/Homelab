# Observability Zone Merge

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

I merged `Security-A` and `MONITOR-A` into the surviving `AlphaSec-Monitor` zone, removed the empty `AlphaSec-Security` zone, and renamed the survivor `AlphaSec-Observability`.

I first repointed the nine policies that named `AlphaSec-Security`. Each preview changed only the intended source or destination zone. UniFi compacted some per-zone-pair indexes after those updates, so I retained both the requested field diff and the observed controller index in the policy ledger. Custom policies stayed at 61 during that phase.

The `Security-A` network move changed its `firewall_zone_id` and caused UniFi to normalize `setting_preference` from `auto` to `manual`. Its network purpose and addressing did not change.

## Stop and correction

I stopped before deleting anything when Prometheus fell from 46 of 46 targets up to 43 of 46. The three failed scrapes were `security-01` node exporter, `security-01` cAdvisor, and `splunk-siem` node exporter.

The live zone readback showed why. A custom zone blocks intra-zone traffic by default in this controller version. The plan's statement that the merged zone would permit the old scrape path was wrong.

I added one narrow replacement policy before removing the old cross-zone policy:

- `Allow Monitor to Security monitoring`
- source `OBJ-Monitor-Collector` in `AlphaSec-Observability`
- destination `OBJ-Security-Stack` on `PG-Node-Exporter` in the same zone
- TCP, logging enabled, index 10000

Prometheus returned to 46 of 46 targets up. The full pre-deletion gate then passed.

The firewall-policy delete preview endpoint mislabeled each delete as a create. I did not confirm those malformed previews. I used the signed-in controller UI to remove the exact old scrape policy and the two redundant egress allows, then proved each policy ID was absent through the controller API.

## Egress collapse

I collapsed the five observability egress policies into these three:

| Index | Policy | Source |
|---:|---|---|
| 10000 | `Allow Observability Web Egress` | `OBJ-Observability-Hosts` |
| 10001 | `Allow Observability NTP Egress` | `OBJ-Observability-Hosts` |
| 10002 | `Block Observability Other External Egress` | `OBJ-Observability-Hosts` |

The controller accepted the terminal block's name and source update but initially retained index 10004. After the redundant web and NTP rules were gone, I used the dedicated ordering API to swap the two non-overlapping allow rules and restore their intended order. That compacted the indexes without placing the terminal block before either allow.

## Final verification

The final controller readback returned 59 custom policies, 14 zones, and 13 firewall groups. `AlphaSec-Security` and both redundant egress policy IDs were absent. `AlphaSec-Observability` remained on controller ID `6a665585052792cd214057cb`.

I repeated the complete service gate after the final reorder:

- Prometheus reported 46 active targets, 46 up, and zero down.
- `app-01` reached Wazuh agent ports TCP 1514 and 1515 on `security-01`.
- `docker-network` received valid redirect responses from Wazuh, Splunk Web, Grafana, PeaNUT, and Prometheus.
- Jedi PC reached `monitor-01` on TCP 3000, 8090, and 9090.
- `ansible-01` reached `monitor-01` on TCP 22.
- `security-01` and `splunk-siem` resolved DNS, returned HTTP 200 over HTTPS, and reported synchronized NTP.
- Both SIEM hosts remained denied on outbound TCP 22 to GitHub.

No S06 stop condition remains active.

## Evidence boundary

The policy ledger retains the exact previews and readbacks for the nine policy updates, and the snapshots retain each structural state. I didn't retain screenshots or a raw interaction transcript for the UI-only network moves, zone deletion, or policy-order adjustment.
