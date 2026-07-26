# Prometheus

**Created:** 2026-07-13  
**Last updated:** 2026-07-26

I run Prometheus & Grafana in Docker on `security-01` at `192.168.72.2`. Prometheus scrapes 44 targets: `node_exporter` on 14 Linux hosts, cAdvisor on all 7 Docker hosts, the Proxmox API exporter, `blackbox_exporter` probes of 19 internal service names, both APC UPS units over NUT, and itself.

**Owner:** Homelab infrastructure monitoring

## Layout

- `Configuration/`: versioned reference configuration matching the live deployment, including the Compose file, `blackbox.yml`, and the whole Grafana provisioning tree.
- `Documentation/Change Records/`: dated implementation and repair records.
- `Documentation/Runbook.md`: routine health checks, configuration changes, dashboard edits, and rollback.
- `Documentation/TODO.md`: current Prometheus backlog.
- `Documentation/Troubleshooting/`: issue index and one dated record per operational problem.
- `Tests/`: validation scripts for the live target set and for every dashboard query.

## Deployed Service

| Item | Value |
|---|---|
| Prometheus UI | `https://prometheus.<YOUR_BASE_DOMAIN>/` through NPM; direct fallback `http://192.168.72.2:9090/` |
| Grafana UI | `https://grafana.<YOUR_BASE_DOMAIN>/`; direct fallback `http://192.168.72.2:3000/` |
| Homelab Overview dashboard | `https://grafana.<YOUR_BASE_DOMAIN>/d/homelab-overview` |
| Live host configuration | `/home/<YOUR_ADMIN_USERNAME>/monitoring/` on `security-01` |
| Versioned configuration | [Configuration/](Configuration/) |
| Versions | Prometheus 3.10.0, Grafana 12.4.1, blackbox_exporter 0.27.0, cAdvisor 0.60.5, node_exporter 1.9.0 |
| Retention | 15 days |
| Scrape intervals | 15s default; 30s for cAdvisor and NUT, 60s for blackbox probes |

## Containers on security-01

`prometheus`, `grafana`, `pve-exporter`, `blackbox-exporter`, and `nut-exporter` run from `~/monitoring/docker-compose.yml`. `cadvisor` runs there too but from its own project at `/opt/docker/cadvisor`, because Ansible owns it across every Docker host identically.

## Scrape Jobs

Jobs are named after the exporter type, with the hostname in a `host` label and a `role` label for dashboard filtering. Before 2026-07-25 there was one job per host, which made `job` double as a hostname and stopped scaling at 14 targets.

| Job | Targets |
|---|---|
| `node` | grey-server, purple-server, blue-server, red-server, security-01, splunk-siem, edge-01, docker-main, ansible-01, docker-blue, media-01, app-01, alpha-prod-01, docker-network |
| `cadvisor` | all 7 Docker hosts: docker-main, docker-network, docker-blue, media-01, alpha-prod-01, app-01, security-01 |
| `proxmox` | PVE API exporter, covering all 21 guests and 10 storages |
| `blackbox` | the 19 service names published through NPM |
| `nut` | both APC Back-UPS Pro BR1500MS2 units, `ups01` on red-server and `ups02` on grey-server |
| `prometheus` | self-scrape |

`kasm-01` is the one running host with no exporter, held back until its move to `purple-server` settles its address.

cAdvisor covers 50 containers across those 7 hosts, 7 of which are the cAdvisor containers themselves. It covered `docker-main` alone from 2026-07-25 to 2026-07-26, because v0.52.1 registers no containers under Docker 29's `overlayfs` driver and `docker-main` was the only Docker host still on `overlay2`. v0.60.5 from `ghcr.io/google/cadvisor` handles the containerd snapshotter. See [the troubleshooting record](Documentation/Troubleshooting/cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md).

## Grafana Configuration Is Versioned

Until 2026-07-25 the datasource and both imported dashboards existed only inside the `grafana_data` Docker volume. Removing that volume would have destroyed all of it with nothing in git to rebuild from.

`Configuration/grafana/` now holds the datasource definition, the dashboard provider, and the Homelab Overview JSON, mounted read-only into the container. `allowUiUpdates` is off, so the repository stays authoritative: to iterate in the browser, use Save As for a scratch copy and fold the change back into the versioned JSON.

The datasource file pins `name: prometheus` and `uid: bfgnkdi47u5tsa` on purpose. Provisioning matches on name, so it adopts the entry that already existed instead of creating a duplicate. The UID was pinned so the two imported dashboards kept resolving; they are gone now, but the pin stays because `homelab-overview.json` references that UID throughout.

## Dashboards

| Dashboard | UID | Purpose |
|---|---|---|
| Homelab Overview | `homelab-overview` | 34 panels in 11 rows, one concern per row: fleet status, services, guests, CPU, memory, storage capacity, drive health, power, containers, network, monitoring health |

One dashboard, provisioned from this repository. On 2026-07-26 I deleted the two imported community dashboards, Node Exporter Full (`rYdddlPWk`, grafana.com 1860) and Proxmox via Prometheus (`Dp7Cd57Zza`, grafana.com 10347). They were the only unversioned dashboards left, so removing them makes the repository the complete record of what Grafana shows.

That cost per-host drill-down, which Node Exporter Full had covered. Rather than re-import 39 panels of someone else's dashboard, I put the drill-down into the versioned one as a **collapsed `Per-host detail` row** driven by a `$host` variable: CPU by mode, load against core count, memory breakdown, swap, every filesystem rather than just root, network per interface, disk throughput, and a host facts table. Collapsed means it costs nothing until expanded, so the overview stays a fleet summary. 34 visible panels, 8 more inside the row, 65 queries in total.

ZFS, SMART, and NVMe deliberately stay out of that row. They already sit under Drive health scoped to `role="hypervisor"`, for the reason below. The disk throughput panel is in the row with a description saying what it means on an LXC guest: `/proc/diskstats` isn't namespaced, so there it reports the hypervisor's physical devices.

Rows are grouped by concern rather than by exporter, so temperature sits with the thing it measures: CPU package temperature under CPU, NVMe temperature under Drive health. Panels run mostly two-across at half width, with heights set from how many series each one draws. Click a row heading to collapse it.

Under each row heading sits a transparent markdown panel with one line about what the section answers and a horizontal rule, because Grafana's row header alone is a thin grey bar that reads as no boundary at all. Those 11 bands are `text` panels with no queries, so `assert_dashboard_queries.py` skips them; the 34 figure above counts data panels only.

Temperatures display in Fahrenheit. `node_hwmon_temp_celsius` reports Celsius, so the panel queries convert with `* 9 / 5 + 32` and their thresholds move with them; changing only the display unit would have labelled a Celsius number as Fahrenheit.

Every hardware panel filters on `role="hypervisor"`. `node_exporter` inside an LXC reports the host's ZFS pools, NVMe SMART data, and disk statistics, because those read from `/sys` and `/proc` paths that aren't namespaced. Unfiltered, one physical ZFS pool appeared as four and four CPUs appeared as thirteen temperature series.

## History

The 2026-07-13 baseline cleanup installed the three missing Proxmox exporters and removed stale jobs: [Security Monitoring Baseline Cleanup - 2026-07-13](Documentation/Change%20Records/Security%20Monitoring%20Baseline%20Cleanup%20-%202026-07-13.md).

On 2026-07-22 I published Prometheus and Grafana through internal NPM and closed the [Grafana plaintext administrator credential incident](../../Security/Incidents/Grafana/Grafana-Incident-Report-2026-07-22-Plaintext-Administrator-Credential.md): [Internal HTTPS Service Onboarding - 2026-07-22](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

The 2026-07-25 expansion took the target set from 7 to 36 and built the overview dashboard. Two follow-ups on 2026-07-26 brought it to 44: enabling UPS collection, then upgrading cAdvisor so the six `overlayfs` hosts report containers. All three are recorded in [Fleet Metrics Expansion and Grafana Overview - 2026-07-25](Documentation/Change%20Records/Fleet%20Metrics%20Expansion%20and%20Grafana%20Overview%20-%202026-07-25.md). Exporter rollout runs from `ansible-01`; the playbooks live in [monitoring-exporters](../Ansible/Source/monitoring-exporters/README.md).
