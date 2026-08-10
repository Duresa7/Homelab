# Prometheus TODO

**Created:** 2026-07-13  
**Last updated:** 2026-08-10

Three items remain open. The 24-hour Grafana lock baseline closed on 2026-07-27 with one successful SQLite retry and zero terminal error lines. The repository no longer carries the inert Grafana WAL setting. The host-side removal remains open until I next recreate Grafana.

## Open

**Repository complete; host pending: retire the inert Grafana WAL setting at the next recreate.** I removed the setting from the versioned Compose file on 2026-08-04. I did not recreate Grafana, so the running Grafana 13.1.1 container keeps the environment value until I next recreate it. This repository change is a no-op for database behavior because the open database was already in rollback-journal mode: header bytes 18 and 19 were `1 1`, and `/var/lib/grafana/` contained `grafana.db` without `grafana.db-wal` or `grafana.db-shm`. The 24-hour window captured on 2026-07-27 contained one `SQLITE_BUSY` retry lasting 9.963223 milliseconds and zero terminal error lines. Repeat the corrected lock count after alert rules add writes. Measurement and earlier lock evidence are in [issue 4](Troubleshooting/Grafana%20SQLite%20Locks%20Under%20Its%20Own%20Housekeeping%20-%202026-07-26.md).

**Collect UniFi gateway, switch, and access-point metrics.** WAN throughput and per-AP client counts are the largest remaining blind spot, and the repository has never enumerated the access points or cameras. `unpoller` needs a read-only UniFi local account, which is a new credential and deserves its own change record rather than being folded into a dashboard task.

**Decide where alerts go, then write rules.** There are no alert rules and no Alertmanager. I kept alerting out of the 2026-07-25 expansion deliberately, because rules that fire into nothing are worse than no rules, so this starts with picking a notification path rather than with writing conditions. The dashboard already encodes the thresholds worth alerting on: targets down, `probe_success == 0`, certificate expiry, ZFS pool state, `nvme_critical_warning`, NVMe spare below 10%, filesystem above 90%, and a UPS off mains.

## Known limits, not tracked as work

Prometheus and Grafana both run floating `:latest` tags. Every exporter is pinned (`blackbox-exporter:v0.28.0`, `ghcr.io/google/cadvisor:v0.60.5`, `prometheus-nut-exporter:1`, `node_exporter` 1.9.0), so the two unpinned images are the older ones. cAdvisor being pinned is what let v0.52.1 sit there registering nothing for a day, and also what makes the upgrade a deliberate, recorded act rather than a surprise.

I checked every component against its upstream release on 2026-07-26. Prometheus 3.13.1, Grafana 13.1.1, and cAdvisor v0.60.5 are the current releases, published 2026-07-10, 2026-07-21, and 2026-07-11. `hon95/prometheus-nut-exporter:1` looks three years stale because it is: v1.2.1 from 2022-08-03 is still the newest release upstream. `blackbox-exporter` was one release behind at v0.27.0 and moved to v0.28.0 the same day.

`node_exporter` stays on the Debian package. All 15 hosts run 1.9.0 while upstream is at v1.12.1 from 2026-07-14, so the fleet sits three minor versions behind on purpose. Debian 13 trixie ships `prometheus-node-exporter` 1.9.0-1+b4, and I decided on 2026-07-26 to keep APT owning the binary rather than move 13 more machines onto a pinned tarball for a version number. Security updates arriving through `apt upgrade` are worth more here than the newer collectors, none of which the dashboard uses. `docker-main` and `splunk-siem` keep the upstream binary because their package managers can't reach 1.9.0 at all. Revisit if trixie backports a newer build, or if a needed collector only exists above 1.9.0.

## Completed

- 2026-08-10: Prometheus restart-policy repair. After CT 104 restarted, Docker skipped Prometheus because its persisted metadata held `HasBeenManuallyStopped=true` under `unless-stopped`. I changed the deployed and live policy to `always`, started it, and verified 52 healthy targets and 20 passing probes. The complete diagnosis is [issue 5](Troubleshooting/Container%20Remained%20Stopped%20After%20monitor-01%20Restart%20-%202026-08-10.md).
- 2026-08-04: Prometheus auto-start verification. During the controlled 2026-08-01 restart, CT 104 booted at 11:11:33 EDT and Prometheus started four seconds later at 11:11:37 EDT with `RestartCount=0`. Grafana started at the same time. Docker was enabled and active, and all seven containers were running with `unless-stopped`, so the boot path rather than a later manual start satisfied the check.
- 2026-07-26: [Monitoring Relocation to monitor-01](Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md). I moved the six-container stack to CT 104 on `blue-server`, added VLAN 73 and `AlphaSec-Monitor`, repointed NPM, retired the old stack, and finished with 46 of 46 targets `up`.
