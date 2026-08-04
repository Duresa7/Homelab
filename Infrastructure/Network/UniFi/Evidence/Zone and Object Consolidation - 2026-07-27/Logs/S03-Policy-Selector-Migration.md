# Firewall Policy Selector Migration

**Created:** 2026-07-27  
**Last updated:** 2026-07-27

I compared each inline selector with its new group's complete member set before changing a policy. The plan's reuse counts included partial overlaps, so replacing every counted selector would have widened or narrowed access. I migrated 35 exact selectors across 24 policies and kept 11 partial or excluded selectors inline.

The first confirmed request used `matching_target: OBJECT`, matching the plugin schema and the plan. The controller rejected it with HTTP 400 because its live enum doesn't contain `OBJECT`. No policy changed. The accepted controller shape is `matching_target: IP`, `matching_target_type: OBJECT`, plus `ip_group_id`; every address migration used that shape.

| Object | Exact policy references after S03 |
|---|---:|
| `OBJ-Monitor-Collector` | 15 |
| `OBJ-Reverse-Proxy` | 7 |
| `OBJ-Security-Stack` | 3 |
| `OBJ-Proxmox-Nodes` | 1 |
| `PG-Node-Exporter` | 3 |
| `PG-Egress-Web` | 3 |
| `PG-NTP` | 3 |

The exact before and after selectors, controller IDs, 11 skipped selectors, and invariant comparison are in `Exports/S03-Policy-Selector-Migration-Ledger.json`. The inter-step snapshots run from `Exports/S03.1-Before-Allow-Automation-to-monitor-01-SSH-Firewall-Snapshot.json` through `Exports/S03.35-After-Final-Firewall-Snapshot.json`.

All 61 policies kept their name, action, enabled state, index, protocol, IP version, logging value, and description value. Every mutation read back with the intended group reference and changed one policy in its structural diff.

## Behavior checks

Prometheus reported 46 of 46 active targets `up`. `monitor-01`, `security-01`, `splunk-siem`, and `docker-network` resolved DNS, reached HTTPS, and reported NTP synchronized.

`docker-network` reached all 19 sockets named by the six NPM backend policies. `ansible-01` reached `monitor-01` on TCP 22. `monitor-01` reached all four Proxmox nodes on TCP 9100 and 8006.

S03 completed with no policy-count, zone-count, group-count, order, action, or enabled-state drift.

## Evidence boundary

The selector ledger preserves the exact before value, requested replacement, preview result, and readback for each policy. I didn't retain a separate raw transport transcript for the 35 confirmed update calls.
