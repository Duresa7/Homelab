# S09 Final Verification

**Created:** 2026-07-27  
**Last updated:** 2026-08-04

## Step S09.1: Read the final controller state

I queried the live controller after S08. The controller returned 361 firewall policies, 59 of them custom, with 58 custom policies enabled. The difference is 302 controller-generated policies. It also returned 14 zones, 25 network objects, 13 firewall groups, 12 client groups, four OON policies, two traffic routes, four WLANs, and four switch port profiles.

I read all 17 routed LAN networks individually and recorded each `firewall_zone_id`. Cluster-Net returned the `AlphaSec-Mgmt` zone ID with DHCP and Internet access both disabled. Security-A and MONITOR-A returned the `AlphaSec-Observability` zone ID. No network returned either deleted zone ID.

The local-only `Exports/S09-Final-Controller-State.json` holds the final controller state.

## Step S09.2: Recheck the service paths

I ran the final path checks from the enforced source systems:

| Source | Check | Observed result |
|---|---|---|
| `grey-server` | `pvecm status` | Four nodes, four votes, quorum 3, `Quorate: Yes` |
| `monitor-01` | Prometheus `/api/v1/targets` | 46 active, 46 up, no down targets |
| `app-01` | TCP 1514 and 1515 to 192.168.72.2 | Both opened |
| `docker-network` | Wazuh, Splunk, Grafana, PeaNUT, and Prometheus backends | HTTP 200 from all five |
| `ansible-01` | TCP 22 to 192.168.73.2 | Opened |
| `security-01` | DNS and HTTPS | GitHub resolved; HTTPS returned 200 |
| `splunk-siem` | DNS and HTTPS | GitHub resolved; HTTPS returned 200 |
| `security-01` | Unapproved TCP 22 egress | Denied |
| `splunk-siem` | Unapproved TCP 22 egress | Denied |

The full S06 gate had already checked the Jedi PC break-glass ports and NTP state after the last firewall ordering change. S07 and S08 did not change those policy bodies.

## Step S09.3: Reconcile the records

I replaced the pre-change VLAN, zone, policy, object, route, WLAN, client-group, and port-profile claims with the final readback. I archived the old 61-policy inventory, the completed network segmentation plan, and both completed execution plans under their matching `Archive/` categories. I kept the dated evidence and change records as historical records.

The consolidation estimate predicted 13 zones. The live controller has 14 because the implementation deleted two zones, not three. I recorded the measured result rather than preserving the estimate.

## Step S09.4: Audit the retained evidence and records

I parsed all 106 JSON evidence files from both execution plans without an error. I checked 40 current and archived Markdown files and every local link resolved after I adjusted the relative paths in the moved records. The 34 records in the execution and archive scope carry an H1, `Created`, and `Last updated` dates. A credential-pattern scan returned no secret value.

`git diff --check` passed. Mission Control's harness ran 1,028 checks and passed. The current firewall inventory contains exactly 59 custom policy rows.

I also repeated the destructive-step readback. VMIDs 103, 300, and 301 were absent from all four Galaxy nodes, and the only backup-capable Proxmox storage returned no archive for any of them.
