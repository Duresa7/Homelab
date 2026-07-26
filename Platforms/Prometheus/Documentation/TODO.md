# Prometheus TODO

**Created:** 2026-07-13  
**Last updated:** 2026-07-26

Six items remain open. Three closed on 2026-07-26: UPS collection, per-container metrics on the six original `overlayfs` hosts, and the relocation of the monitoring stack to CT 104 `monitor-01` on `blue-server`. I record future monitoring changes here before promoting them to an active project.

## Open

**Baseline the Grafana lock errors on 2026-07-27, then decide what to do about WAL.** Run `docker logs --since 24h grafana 2>&1 | grep -c "level=error"` on `monitor-01`. `GF_DATABASE_WAL=true` does nothing on Grafana 13.1.1, so this measures an unmitigated database rather than proving a fix: header bytes 18 and 19 of `grafana.db` read `1 1`, and no `-wal` file exists. Near zero means dropping the dead setting at the next recreate. Anything else means setting `PRAGMA journal_mode=WAL` on the file, which persists but adds a manual step to every rebuild, or moving to Postgres. Reasoning & evidence in [issue 4](Troubleshooting/Grafana%20SQLite%20Locks%20Under%20Its%20Own%20Housekeeping%20-%202026-07-26.md). Do this before writing alert rules, because saving rules was one of the failing jobs on 12.4.1.

**Fix two UniFi entries that the API can't reach.** Both need the controller UI. The custom zone for VLAN 73 is named `Org-Monitor`, which came from reading this repository's `<YOUR_ORG_NAME>` redaction placeholder literally; every sibling zone is `<YOUR_ORG_NAME>-Servers`, `<YOUR_ORG_NAME>-Mgmt`, `<YOUR_ORG_NAME>-Security`, `<YOUR_ORG_NAME>-Access`, or `<YOUR_ORG_NAME>-Cluster`, so it should be `<YOUR_ORG_NAME>-Monitor`. Separately, policy `6a60fd2c2d027bb05525a876` is now scoped to TCP 443 alone but still describes itself as reaching "Wazuh, Grafana, and Prometheus on security-01"; the name should lose the plural too. Renaming a zone doesn't touch policy bindings, which reference it by `zone_id`.

**Decide whether `node_exporter` leaves the Debian package.** Every one of the 15 hosts runs 1.9.0. Upstream is at v1.12.1, released 2026-07-14, so the fleet is three minor versions behind. This isn't drift: Debian 13 trixie ships `prometheus-node-exporter` 1.9.0-1+b4, and the [Ansible project](../../Ansible/Source/monitoring-exporters/README.md) picks the package on any host whose APT candidate is 1.9.0 specifically so trixie hosts stay under the package manager. Taking 1.12.1 means every host moves to the upstream binary path that only `docker-main` and `splunk-siem` use today, which trades APT's security updates for a pinned tarball on 13 more machines. The dashboard aggregates across hosts, so it's all of them or none. Nothing is broken at 1.9.0; decide this on its merits rather than because a newer number exists.

**Scrape `kasm-01`.** It's the one running host with no `node_exporter`. It sits outside the Ansible inventory, and the move to `purple-server` in [Kasm Relocation to Purple](../../Kasm%20Workspaces/Documentation/Change%20Plans/) is still open, so its address may change. Adding it now means redoing the inventory entry and the firewall scope afterward.

**Collect UniFi gateway, switch, and access-point metrics.** WAN throughput and per-AP client counts are the largest remaining blind spot, and the repository has never enumerated the access points or cameras. `unpoller` needs a read-only UniFi local account, which is a new credential in 1Password and deserves its own change record rather than being folded into a dashboard task.

**Decide where alerts go, then write rules.** There are no alert rules and no Alertmanager. I kept alerting out of the 2026-07-25 expansion deliberately, because rules that fire into nothing are worse than no rules, so this starts with picking a notification path rather than with writing conditions. The dashboard already encodes the thresholds worth alerting on: targets down, `probe_success == 0`, certificate expiry, ZFS pool state, `nvme_critical_warning`, NVMe spare below 10%, filesystem above 90%, and a UPS off mains.

## Known limits, not tracked as work

Prometheus and Grafana both run floating `:latest` tags. Every exporter is pinned (`blackbox-exporter:v0.28.0`, `ghcr.io/google/cadvisor:v0.60.5`, `prometheus-nut-exporter:1`, `node_exporter` 1.9.0), so the two unpinned images are the older ones. cAdvisor being pinned is what let v0.52.1 sit there registering nothing for a day, and also what makes the upgrade a deliberate, recorded act rather than a surprise.

I checked every component against its upstream release on 2026-07-26. Prometheus 3.13.1, Grafana 13.1.1, and cAdvisor v0.60.5 are the current releases, published 2026-07-10, 2026-07-21, and 2026-07-11. `hon95/prometheus-nut-exporter:1` looks three years stale because it is: v1.2.1 from 2022-08-03 is still the newest release upstream. `blackbox-exporter` was one release behind at v0.27.0 and moved to v0.28.0 the same day. `node_exporter` is the one real gap, below.

## Completed

- 2026-07-26: [Monitoring Relocation to monitor-01](Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md). I moved the six-container stack to CT 104 on `blue-server`, added VLAN 73 and `Org-Monitor`, repointed NPM, retired the old stack, and finished with 46 of 46 targets `up`.
