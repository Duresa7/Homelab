# Prometheus TODO

**Created:** 2026-07-13  
**Last updated:** 2026-07-27

Four items remain open. The 24-hour Grafana lock baseline closed on 2026-07-27 with one successful SQLite retry and zero terminal error lines; removing the inactive WAL setting at the next recreate replaces that measurement task.

## Open

**Remove `GF_DATABASE_WAL=true` at the next Grafana recreate.** Grafana 13.1.1 reads the variable but leaves SQLite in rollback-journal mode. The 24-hour window captured on 2026-07-27 contained one `SQLITE_BUSY` retry lasting 9.963223 milliseconds and zero terminal error lines. I left the running container alone because removing an inactive variable provides no service benefit until another recreate is required. Repeat the corrected lock count after alert rules add writes. Reasoning & evidence in [issue 4](Troubleshooting/Grafana%20SQLite%20Locks%20Under%20Its%20Own%20Housekeeping%20-%202026-07-26.md).

**Scrape `kasm-01`.** It's the one running host with no `node_exporter`. It sits outside the Ansible inventory, and the move to `purple-server` in [Kasm Relocation to Purple](../../Kasm%20Workspaces/Documentation/Change%20Plans/) is still open, so its address may change. Adding it now means redoing the inventory entry and the firewall scope afterward.

**Collect UniFi gateway, switch, and access-point metrics.** WAN throughput and per-AP client counts are the largest remaining blind spot, and the repository has never enumerated the access points or cameras. `unpoller` needs a read-only UniFi local account, which is a new credential in 1Password and deserves its own change record rather than being folded into a dashboard task.

**Decide where alerts go, then write rules.** There are no alert rules and no Alertmanager. I kept alerting out of the 2026-07-25 expansion deliberately, because rules that fire into nothing are worse than no rules, so this starts with picking a notification path rather than with writing conditions. The dashboard already encodes the thresholds worth alerting on: targets down, `probe_success == 0`, certificate expiry, ZFS pool state, `nvme_critical_warning`, NVMe spare below 10%, filesystem above 90%, and a UPS off mains.

## Known limits, not tracked as work

Prometheus and Grafana both run floating `:latest` tags. Every exporter is pinned (`blackbox-exporter:v0.28.0`, `ghcr.io/google/cadvisor:v0.60.5`, `prometheus-nut-exporter:1`, `node_exporter` 1.9.0), so the two unpinned images are the older ones. cAdvisor being pinned is what let v0.52.1 sit there registering nothing for a day, and also what makes the upgrade a deliberate, recorded act rather than a surprise.

I checked every component against its upstream release on 2026-07-26. Prometheus 3.13.1, Grafana 13.1.1, and cAdvisor v0.60.5 are the current releases, published 2026-07-10, 2026-07-21, and 2026-07-11. `hon95/prometheus-nut-exporter:1` looks three years stale because it is: v1.2.1 from 2022-08-03 is still the newest release upstream. `blackbox-exporter` was one release behind at v0.27.0 and moved to v0.28.0 the same day.

`node_exporter` stays on the Debian package. All 15 hosts run 1.9.0 while upstream is at v1.12.1 from 2026-07-14, so the fleet sits three minor versions behind on purpose. Debian 13 trixie ships `prometheus-node-exporter` 1.9.0-1+b4, and I decided on 2026-07-26 to keep APT owning the binary rather than move 13 more machines onto a pinned tarball for a version number. Security updates arriving through `apt upgrade` are worth more here than the newer collectors, none of which the dashboard uses. `docker-main` and `splunk-siem` keep the upstream binary because their package managers can't reach 1.9.0 at all. Revisit if trixie backports a newer build, or if a needed collector only exists above 1.9.0.

## Completed

- 2026-07-26: [Monitoring Relocation to monitor-01](Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md). I moved the six-container stack to CT 104 on `blue-server`, added VLAN 73 and `<YOUR_ORG_NAME>`-Monitor, repointed NPM, retired the old stack, and finished with 46 of 46 targets `up`.
