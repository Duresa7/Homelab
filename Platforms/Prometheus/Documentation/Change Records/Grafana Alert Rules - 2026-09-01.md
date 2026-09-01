# Grafana Alert Rules

**Created:** 2026-09-01  
**Last updated:** 2026-09-01

**Implementation started:** 2026-08-31  
**Completed:** 2026-09-01  
**Status:** Rules complete; notification destination open  
**Affected systems:** Grafana and Prometheus on `monitor-01`

## Change

I added 12 file-provisioned Grafana alert rules under `Homelab Alerts`. Grafana evaluates them through the existing Prometheus datasource, so this adds no Alertmanager container and no new credential. The file is mounted read-only with the rest of Grafana provisioning and remains the source of truth.

| Group | Rules | Evaluation interval |
|---|---:|---:|
| Availability | Host down, exporter down, internal service unreachable, Proxmox node or cluster down | 1 minute |
| Capacity | Filesystem, Proxmox storage, memory, disk saturation | 5 minutes |
| Network | Internal service latency | 1 minute |
| Power and hardware | UPS on battery, UPS battery fault, high temperature | 1 minute |

The thresholds came from the live 2026-08-31 values rather than a generic template. Filesystems and Proxmox storage alert above 85%, memory above 92%, sustained disk busy time above 95%, blackbox response time above five seconds, and hypervisor temperature above 80 C. Availability and UPS rules use the metric's binary state. Every rule has a `for` window so a single scrape or short load spike does not fire it.

## Deployment

I deployed the initial file before Grafana's 2026-08-31 fleet-update recreation. Grafana 13.2.0 logged a completed alert-provisioning pass, initialized 12 rules, and started the scheduler.

The repository copy received one final revision five minutes after the first upload. The first inline retry was too large for the Executor proxy and returned HTTP 504 without changing the live hash. I compressed that same file, uploaded the small archive through SSH Manager, verified the uncompressed SHA-256 before replacement, atomically replaced the live YAML, removed the archive, and called Grafana's authenticated alert-provisioning reload endpoint. The reload returned HTTP 200 and Grafana logged `finished to provision alerting` without an error.

The old alerting `.gitkeep` was no longer a placeholder once the YAML existed. I removed it from the repository and host so Grafana no longer logs an invalid-suffix warning for that directory.

The final consistency pass found four dead UPS-01 panels on the generated `red-server` dashboard and stale two-UPS wording on the overview and power dashboards. I removed the inactive capability from the dashboard inventory, regenerated all 27 dashboards, and retained UPS-01's restoration instructions in the Prometheus configuration and backlog. I deployed the three changed JSON files without restarting Grafana; their live SHA-256 values matched the repository, and authenticated dashboard API responses contained zero `ups01` mentions or `Power` rows on `red-server`.

## Verification

- YAML parsing found four groups, 12 unique rule UIDs, and 12 rules.
- The deployed file and repository file share SHA-256 `f20cce12ed5c7d24083e7bde6898ddf47f3ef40ed773b20dcc0cce186bde4108`.
- All 12 PromQL expressions returned a successful response from Prometheus 3.14.0.
- The healthy baseline evaluated 18 host series, 19 blackbox services, six Proxmox node or cluster series, 31 filesystems, 13 Proxmox storages, five hypervisor disk and temperature series, and UPS-02. Zero series crossed a rule threshold.
- Grafana's database held 12 alert rules and 12 rule-state rows with zero rule-instance errors before the final reload; the completed reload retained the same 12 UIDs.
- Prometheus reported 49 active targets with all 49 `up`. Grafana reported version 13.2.0 and database state `ok`.
- All 27 regenerated dashboards passed the layout check; 1,390 PromQL queries returned 1,385 populated results, five expected empty results, zero unexpected empty results, and zero errors.

I created no snapshot or backup. The versioned YAML rebuilds the rule definitions, and the Grafana data volume retains evaluation state.

## Remaining Work

I have not configured an external contact point or a tested routing policy. A firing rule is visible in Grafana but is not delivered elsewhere. Selecting the destination, provisioning its credential outside the repository, and proving one bounded test notification remain in the [Prometheus backlog](../TODO.md).
