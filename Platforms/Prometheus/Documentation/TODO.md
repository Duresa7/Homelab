# Prometheus TODO

**Created:** 2026-07-13  
**Last updated:** 2026-07-26

Five items open. Two closed on 2026-07-26: UPS collection, once the Proxmox cluster firewall permitted `192.168.72.2` to TCP 3493, and per-container metrics on the six `overlayfs` hosts, once cAdvisor moved to v0.60.5. I record future monitoring changes here before promoting them to an active project.

## Open

**Confirm the Grafana WAL fix held, on 2026-07-27.** Run `docker logs --since 24h grafana 2>&1 | grep -c "level=error"` on `security-01`. The baseline to beat is 25 errors in 10 hours, all `database is locked`. At or near zero closes [issue 4](Troubleshooting/Grafana%20SQLite%20Locks%20Under%20Its%20Own%20Housekeeping%20-%202026-07-26.md); anything else means the diagnosis was wrong and an external database is the next step. Do this before writing alert rules, because saving rules was one of the failing jobs.

**Move Prometheus and Grafana off `grey-server`.** `security-01` sits on the node that also holds `app-01`, `docker-main`, and `splunk-siem`, so Grey failing takes monitoring down along with most of what it monitors. The target is CT 104 `monitor-01`, a Debian 13 LXC on `blue-server` with 2 cores and 2 GiB, on a new VLAN 73 `MONITOR-A` in a new `Org-Monitor` zone. Ten phases, twenty-three firewall changes across two systems, and the hard gate before cutover are in [Move Monitoring off grey-server](Change%20Plans/Move%20Monitoring%20off%20grey-server.md). Written to be handed to an agent. Sequenced after alerting on purpose.

**Scrape `kasm-01`.** It's the one running host with no `node_exporter`. It sits outside the Ansible inventory, and the move to `purple-server` in [Kasm Relocation to Purple](../../Kasm%20Workspaces/Documentation/Change%20Plans/) is still open, so its address may change. Adding it now means redoing the inventory entry and the firewall scope afterward.

**Collect UniFi gateway, switch, and access-point metrics.** WAN throughput and per-AP client counts are the largest remaining blind spot, and the repository has never enumerated the access points or cameras. `unpoller` needs a read-only UniFi local account, which is a new credential in 1Password and deserves its own change record rather than being folded into a dashboard task.

**Decide where alerts go, then write rules.** There are no alert rules and no Alertmanager. I kept alerting out of the 2026-07-25 expansion deliberately, because rules that fire into nothing are worse than no rules, so this starts with picking a notification path rather than with writing conditions. The dashboard already encodes the thresholds worth alerting on: targets down, `probe_success == 0`, certificate expiry, ZFS pool state, `nvme_critical_warning`, NVMe spare below 10%, filesystem above 90%, and a UPS off mains.

## Known limits, not tracked as work

Prometheus and Grafana both run floating `:latest` tags. Every exporter is pinned (`blackbox-exporter:v0.27.0`, `ghcr.io/google/cadvisor:v0.60.5`, `prometheus-nut-exporter:1`, `node_exporter` 1.9.0), so the two unpinned images are the older ones. cAdvisor being pinned is what let v0.52.1 sit there registering nothing for a day, and also what makes the upgrade a deliberate, recorded act rather than a surprise.
