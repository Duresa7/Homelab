# Prometheus

**Created:** 2026-07-13  
**Last updated:** 2026-08-10

I run Prometheus & Grafana in Docker on CT 104 `monitor-01` at `192.168.73.2`. Prometheus 3.13.1 scrapes 52 targets: `node_exporter` on 19 Linux hosts, cAdvisor on all 9 Docker hosts, the Proxmox API exporter, `blackbox_exporter` probes of 20 internal service names, both APC UPS units over NUT, and itself. All 52 were `UP` during the 2026-08-10 post-restart check. TeamSpeak voice reachability arrives as node_exporter textfile metrics from `alpha-prod-01` rather than a scrape target, so those six public and local UDP checks add series without changing the target count: see [TeamSpeak Reachability Monitoring - 2026-07-28](../Teamspeak%20Hosting/Documentation/Change%20Records/TeamSpeak%20Reachability%20Monitoring%20-%202026-07-28.md).

The [Galaxy Green baseline and monitoring record](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Green%20Baseline%20and%20Monitoring%20-%202026-07-31.md) contains the 2026-07-31 rollout, rollback checks, and live 49-target validation.

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
| Prometheus UI | `https://prometheus.alphasecunited.com/` through NPM; direct fallback `http://192.168.73.2:9090/` |
| Grafana UI | `https://grafana.alphasecunited.com/`; direct fallback `http://192.168.73.2:3000/` |
| Homelab Overview dashboard | `https://grafana.alphasecunited.com/d/homelab-overview` |
| Live host configuration | `/home/dkadi/monitoring/` on `monitor-01` |
| Versioned configuration | [Configuration/](Configuration/) |
| Versions | Prometheus 3.13.1, Grafana 13.1.1, blackbox_exporter 0.28.0, cAdvisor 0.60.5, node_exporter 1.9.0 |
| Retention | 15 days |
| Scrape intervals | 15s default; 30s for cAdvisor and NUT, 60s for blackbox probes |

## Containers on monitor-01

Seven containers run on the host from three Compose projects. `prometheus`, `grafana`, `pve-exporter`, `blackbox-exporter`, and `nut-exporter` come from `~/monitoring/docker-compose.yml`. `cadvisor` comes from `/opt/docker/cadvisor`, deployed by the same Ansible playbook that manages the other eight Docker hosts. PeaNUT runs from `/opt/docker/peanut`.

The 2026-08-10 restart exposed a limit in the old policy: Docker held `HasBeenManuallyStopped=true` for Prometheus, so `unless-stopped` skipped it while the other containers returned. I changed Prometheus alone to `restart: always`, started it, and verified both readiness paths, 52 healthy targets, and 20 passing probes. The diagnosis and correction are in [issue 5](Documentation/Troubleshooting/Container%20Remained%20Stopped%20After%20monitor-01%20Restart%20-%202026-08-10.md).

## Scrape Jobs

Jobs are named after the exporter type, with the hostname in a `host` label and a `role` label for dashboard filtering. Before 2026-07-25 there was one job per host, which made `job` double as a hostname and stopped scaling at 14 targets.

| Job | Targets |
|---|---|
| `node` | grey-server, purple-server, blue-server, red-server, green-server, security-01, splunk-siem, edge-01, docker-main, ansible-01, docker-blue, media-01, app-01, alpha-prod-01, docker-network, monitor-01, kasm-01, debian-dev (configured `host` label `db-13-dev`), game-01 |
| `cadvisor` | all 9 Docker hosts: docker-main, docker-network, docker-blue, media-01, alpha-prod-01, app-01, security-01, monitor-01, game-01 |
| `proxmox` | PVE API exporter, covering Galaxy nodes, guests, and storages dynamically |
| `blackbox` | the 20 service names published through NPM |
| `nut` | both APC Back-UPS Pro BR1500MS2 units, `ups01` on red-server and `ups02` on grey-server |
| `prometheus` | self-scrape |

`kasm-01` gained `node_exporter` 1.9.0 on 2026-07-28 and is the one host whose exporter binds a single address, `192.168.78.10:9100`, instead of every interface. It holds macvlan shim addresses inside the three sealed lab lanes, and an exporter on 0.0.0.0 would answer a session container sharing one of those subnets, where the gateway never sees the packets. One policy lets `192.168.73.2` reach that port and nothing else. The LAB-MGMT-to-observability block had to narrow to `NEW, INVALID` for the scrape to work, because a block matching all states also dropped the replies.

Every other host still exports on all interfaces, which is why the playbook's bind address is an inventory override rather than a fleet default.

cAdvisor covers 53 named containers across those 8 hosts, 8 of which are the cAdvisor containers themselves. A 2026-07-28 Prometheus query returned 11 on `docker-main`, 5 on `docker-network`, 4 on `docker-blue`, 10 on `media-01`, 8 on `alpha-prod-01`, 7 on `app-01`, 1 on `security-01`, & 7 on `monitor-01`. cAdvisor covered `docker-main` alone from 2026-07-25 to 2026-07-26, because v0.52.1 registers no containers under Docker 29's `overlayfs` driver and `docker-main` was the only Docker host still on `overlay2`. v0.60.5 from `ghcr.io/google/cadvisor` handles the containerd snapshotter. See [the troubleshooting record](Documentation/Troubleshooting/cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md).

## Grafana Configuration Is Versioned

Until 2026-07-25 the datasource and both imported dashboards existed only inside the `grafana_data` Docker volume. Removing that volume would have destroyed all of it with nothing in git to rebuild from.

`Configuration/grafana/` now holds the datasource definition, the dashboard provider, and the Homelab Overview JSON, mounted read-only into the container. `allowUiUpdates` is off, so the repository stays authoritative: to iterate in the browser, use Save As for a scratch copy and fold the change back into the versioned JSON.

The datasource file pins `name: prometheus` and `uid: bfgnkdi47u5tsa` on purpose. Provisioning matches on name, so it adopts the entry that already existed instead of creating a duplicate. The UID was pinned so the two imported dashboards kept resolving; they are gone now, but the pin stays because `homelab-overview.json` references that UID throughout.

## Dashboards

| Dashboard | UID | Purpose |
|---|---|---|
| Homelab Overview | `homelab-overview` | 34 visible panels across 11 concern rows: fleet status, services, guests, CPU, memory, storage capacity, drive health, power, containers, network, monitoring health. A twelfth row, `Per-host detail`, stays collapsed and holds 8 more |

One dashboard, provisioned from this repository. On 2026-07-26 I deleted the two imported community dashboards, Node Exporter Full (`rYdddlPWk`, grafana.com 1860) and Proxmox via Prometheus (`Dp7Cd57Zza`, grafana.com 10347). They were the only unversioned dashboards left, so removing them makes the repository the complete record of what Grafana shows.

That cost per-host drill-down, which Node Exporter Full had covered. Rather than re-import 39 panels of someone else's dashboard, I put the drill-down into the versioned one as a **collapsed `Per-host detail` row** driven by a `$host` variable: CPU by mode, load against core count, memory breakdown, swap, every filesystem rather than just root, network per interface, disk throughput, and a host facts table. Collapsed means it costs nothing until expanded, so the overview stays a fleet summary. 34 visible panels, 8 more inside the row, 65 queries in total.

ZFS, SMART, and NVMe deliberately stay out of that row. They already sit under Drive health scoped to `role="hypervisor"`, for the reason below. The disk throughput panel is in the row with a description saying what it means on an LXC guest: `/proc/diskstats` isn't namespaced, so there it reports the hypervisor's physical devices.

Rows are grouped by concern rather than by exporter, so temperature sits with the thing it measures: CPU package temperature under CPU, NVMe temperature under Drive health. Panels run mostly two-across at half width, with heights set from how many series each one draws. Click a row heading to collapse it.

Under each row heading sits a transparent markdown panel with one line about what the section answers and a horizontal rule, because Grafana's row header alone is a thin grey bar that reads as no boundary at all. Those 11 bands are `text` panels with no queries, so `assert_dashboard_queries.py` skips them; the 34 figure above counts data panels only.

Temperatures display in Fahrenheit. `node_hwmon_temp_celsius` reports Celsius, so the panel queries convert with `* 9 / 5 + 32` and their thresholds move with them; changing only the display unit would have labelled a Celsius number as Fahrenheit.

Every hardware panel filters on `role="hypervisor"`. `node_exporter` inside an LXC reports the host's ZFS pools, NVMe SMART data, and disk statistics, because those read from `/sys` and `/proc` paths that aren't namespaced. Unfiltered, one physical ZFS pool appeared as four and four CPUs appeared as thirteen temperature series.

## History

The 2026-07-13 baseline cleanup installed the three missing Proxmox exporters and removed stale jobs: [Security Monitoring Baseline Cleanup - 2026-07-13](Documentation/Change%20Records/Security%20Monitoring%20Baseline%20Cleanup%20-%202026-07-13.md).

On 2026-07-22 I published Prometheus and Grafana through internal NPM and closed the [Grafana plaintext administrator credential incident](../../Security/Incidents/Grafana/Plaintext%20Administrator%20Credential%20-%202026-07-22.md): [Internal HTTPS Service Onboarding - 2026-07-22](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

The 2026-07-25 expansion took the target set from 7 to 36 and built the overview dashboard. Two follow-ups on 2026-07-26 brought it to 44: enabling UPS collection, then upgrading cAdvisor so the six `overlayfs` hosts report containers. All three are recorded in [Fleet Metrics Expansion and Grafana Overview - 2026-07-25](Documentation/Change%20Records/Fleet%20Metrics%20Expansion%20and%20Grafana%20Overview%20-%202026-07-25.md). Exporter rollout runs from `ansible-01`; the playbooks live in [monitoring-exporters](../Ansible/Source/monitoring-exporters/README.md).

On 2026-07-26 I moved the stack from `security-01` on `grey-server` to CT 104 `monitor-01` on `blue-server`, added the new host's two exporters, and retired the old monitoring files and volumes. The final target set is 46 of 46 `up`: [Monitoring Relocation to monitor-01 - 2026-07-26](Documentation/Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md).
