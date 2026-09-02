# Prometheus

**Created:** 2026-07-13  
**Last updated:** 2026-09-02

I run Prometheus & Grafana in Docker on CT 104 `monitor-01` at `192.168.73.2`. Prometheus 3.14.0 scrapes 49 targets: `node_exporter` on 18 Linux hosts, cAdvisor on all 9 Docker hosts, the Proxmox API exporter, `blackbox_exporter` probes of 19 internal service names, UPS-02 over NUT, and itself. TeamSpeak voice reachability arrives as node_exporter textfile metrics from `alpha-prod-01` rather than a scrape target, so those six public and local UDP checks add series without changing the target count: see [TeamSpeak Reachability Monitoring - 2026-07-28](../Teamspeak%20Hosting/Documentation/Change%20Records/TeamSpeak%20Reachability%20Monitoring%20-%202026-07-28.md).

The [Galaxy Green baseline and monitoring record](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Green%20Baseline%20and%20Monitoring%20-%202026-07-31.md) contains the 2026-07-31 rollout, rollback checks, and live 49-target validation.

**Owner:** Homelab infrastructure monitoring

## Layout

- `Configuration/`: versioned reference configuration matching the live deployment, including the Compose file, `blackbox.yml`, and the whole Grafana provisioning tree.
- `Documentation/Change Records/`: dated implementation and repair records.
- `Documentation/Runbook.md`: routine health checks, configuration changes, dashboard edits, and rollback.
- `Documentation/TODO.md`: current Prometheus backlog.
- `Documentation/Troubleshooting/`: issue index and one dated record per operational problem.
- `Tests/`: validation scripts for the live target set, for every dashboard query, and for dashboard layout.
- `Tools/`: the dashboard generator. The JSON under `Configuration/grafana/dashboards/` is its output.

## Deployed Service

| Item | Value |
|---|---|
| Prometheus UI | `https://prometheus.alphasecunited.com/` through NPM; direct fallback `http://192.168.73.2:9090/` |
| Grafana UI | `https://grafana.alphasecunited.com/`; direct fallback `http://192.168.73.2:3000/` |
| Homelab Overview dashboard | `https://grafana.alphasecunited.com/d/homelab-overview` |
| A host's own dashboard | `https://grafana.alphasecunited.com/d/node-<host>`, e.g. `/d/node-grey-server` |
| Live host configuration | `/home/dkadi/monitoring/` on `monitor-01` |
| Versioned configuration | [Configuration/](Configuration/) |
| Versions | Prometheus 3.14.0, Grafana 13.2.0, blackbox_exporter 0.28.0, cAdvisor 0.60.5, node_exporter 1.9.0 |
| Retention | 15 days |
| Scrape intervals | 15s default; 30s for cAdvisor and NUT, 60s for blackbox probes |

## Containers on monitor-01

Seven containers run on the host from three Compose projects. `prometheus`, `grafana`, `pve-exporter`, `blackbox-exporter`, and `nut-exporter` come from `~/monitoring/docker-compose.yml`. `cadvisor` comes from `/opt/docker/cadvisor`, deployed by the same Ansible playbook that manages the other eight Docker hosts. PeaNUT runs from `/opt/docker/peanut`.

The 2026-08-10 restart exposed a limit in the old policy: Docker held `HasBeenManuallyStopped=true` for Prometheus, so `unless-stopped` skipped it while the other containers returned. I changed Prometheus alone to `restart: always`, started it, and verified both readiness paths, 52 healthy targets, and 20 passing probes. The diagnosis and correction are in [issue 5](Documentation/Troubleshooting/Container%20Remained%20Stopped%20After%20monitor-01%20Restart%20-%202026-08-10.md).

## Scrape Jobs

Jobs are named after the exporter type, with the hostname in a `host` label and a `role` label for dashboard filtering. Before 2026-07-25 there was one job per host, which made `job` double as a hostname and stopped scaling at 14 targets.

| Job | Targets |
|---|---|
| `node` | grey-server, purple-server, blue-server, red-server, green-server, security-01, splunk-siem, edge-01, docker-main, ansible-01, docker-blue, media-01, app-01, alpha-prod-01, docker-network, monitor-01, ubuntu-dev (configured `host` label `ubuntu-dev`), game-01 |
| `cadvisor` | all 9 Docker hosts: docker-main, docker-network, docker-blue, media-01, alpha-prod-01, app-01, security-01, monitor-01, game-01 |
| `proxmox` | PVE API exporter, covering Galaxy nodes, guests, and storages dynamically |
| `blackbox` | the 19 service names published through NPM |
| `nut` | APC Back-UPS Pro BR1500MS2 UPS-02 on grey-server; UPS-01 left the target set on 2026-08-31 while its data cable remains disconnected |
| `prometheus` | self-scrape |

The current target set has no retired lab endpoints. The retained node-exporter
targets use the all-interface listener expected by the automation. Prometheus has
its administrative API disabled, no historical label from the retired lab
workload, and all 49 targets up.

cAdvisor covers 53 named containers across those 8 hosts, 8 of which are the cAdvisor containers themselves. A 2026-07-28 Prometheus query returned 11 on `docker-main`, 5 on `docker-network`, 4 on `docker-blue`, 10 on `media-01`, 8 on `alpha-prod-01`, 7 on `app-01`, 1 on `security-01`, & 7 on `monitor-01`. cAdvisor covered `docker-main` alone from 2026-07-25 to 2026-07-26, because v0.52.1 registers no containers under Docker 29's `overlayfs` driver and `docker-main` was the only Docker host still on `overlay2`. v0.60.5 from `ghcr.io/google/cadvisor` handles the containerd snapshotter. See [the troubleshooting record](Documentation/Troubleshooting/cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md).

## Grafana Configuration Is Versioned

Until 2026-07-25 the datasource and both imported dashboards existed only inside the `grafana_data` Docker volume. Removing that volume would have destroyed all of it with nothing in git to rebuild from.

`Configuration/grafana/` now holds the datasource definition, the dashboard providers, all 27 dashboards, and 12 Grafana-managed alert rules, mounted read-only into the container. `allowUiUpdates` is off, so the repository stays authoritative.

The 15 rules cover host, exporter, service, Proxmox node and named guest availability; filesystem, Proxmox storage, memory, CPU, load and disk capacity; service latency; UPS state; and hardware temperature. Grafana holds all 15 as file-provisioned rules with no evaluation error, and no threshold is crossed against live data as of 2026-09-02. I have not configured an external notification destination, so the remaining alerting decision is where Grafana should deliver a firing rule. The implementation and verification are in [Grafana Alert Rules - 2026-09-01](Documentation/Change%20Records/Grafana%20Alert%20Rules%20-%202026-09-01.md) and [Guest, CPU and Load Alert Rules - 2026-09-02](Documentation/Change%20Records/Guest%20CPU%20and%20Load%20Alert%20Rules%20-%202026-09-02.md).

Since 2026-08-27 there are two providers, because eighteen node dashboards in the same folder as the overview would bury it, and because the header dropdowns filter by tag. Their paths must not nest: Grafana's file provider walks its path recursively, so a provider pointing at the parent would claim the node dashboards too and the two would fight over the same files on every scan.

The dashboards carry `"editable": true`, which is not a contradiction with `allowUiUpdates: false`. Provisioning still refuses to persist a browser edit; leaving the flag on keeps panel-edit and Explore reachable so a query can be read without hunting for it in git. To iterate, change the generator and re-run it — a hand edit to a file under `dashboards/` is overwritten by the next build.

The datasource file pins `name: prometheus` and `uid: bfgnkdi47u5tsa` on purpose. Provisioning matches on name, so it adopts the entry that already existed instead of creating a duplicate. The UID was pinned so the two imported dashboards kept resolving; they are gone now, but the pin stays because `homelab-overview.json` references that UID throughout.

## Dashboards

27 dashboards in two Grafana folders, all generated from [Tools/](Tools/README.md) and committed here.

| Folder | Dashboard | UID | Purpose |
|---|---|---|---|
| Homelab | Homelab Overview | `homelab-overview` | Eight health tiles, one table of everything failing a check, the fleet table, service reachability, and links out |
| Homelab | Proxmox · Galaxy Cluster | `proxmox-cluster` | Quorum, the five nodes, every guest, guest I/O, every storage |
| Homelab | Containers | `containers` | 56 containers across the nine cAdvisor hosts, with restart and OOM tables |
| Homelab | Services & Uptime | `services-uptime` | The 19 names through NPM: reachability, latency by request phase, TLS expiry |
| Homelab | Storage & Drive Health | `storage-health` | Capacity and days-to-full first, then NVMe, SATA SMART and ZFS |
| Homelab | Network | `network` | Throughput, errors and drops, TCP state, connection tracking |
| Homelab | Power & UPS | `power-ups` | UPS-02 battery, runtime, load, mains, and status flags; UPS-01 is absent while its data cable remains disconnected |
| Homelab | Monitoring Health | `monitoring-health` | Target health, scrape cost, TSDB growth, the 18 node_exporters |
| Homelab | TeamSpeak | `teamspeak` | ts02 and ts03, with the fault isolated to the server or the path in front of it |
| Nodes | one per host | `node-<host>` | Status, CPU, memory, filesystems, disk, network, then whatever else that host has |

Every header carries two dashboard-link dropdowns filtered by tag — **Homelab** lists the nine, **Nodes** the
eighteen — and both keep the current time range. Any table with a hostname in it links that column to that
host's dashboard, so the fleet table, the guest table, the storage tables and the target list are all routes
into a node board.

### One dashboard per host

Eighteen of the 27 are per-host. Each is a real dashboard with its own UID and its own entry in the folder,
not a `$host` filter on a shared one, because a host is a thing you open rather than a variable you set — and
because a filter can only show what is true of every host. A per-host board can show `grey-server`'s ZFS pool,
`media-01`'s containers, `red-server`'s UPS and `blue-server`'s NVMe, and omit each of those from the fifteen
hosts they are not true of.

They are generated rather than written for the obvious reason: eighteen hand-kept copies of one layout
diverge the first time one is edited. The layout lives once in `Tools/build_dashboards.py` and the capability
flags in `Tools/inventory.py` decide which sections each host grows.

### Conventions

Panel type follows the data's job: a stat tile for one current value, a bar gauge for a ratio against a limit,
a time series for change over time, a state timeline for up-or-down over time, a table with in-cell bars for
one row per thing, and a table with a written-out empty state for a list that should normally be empty. Above
eight series a time series shows `topk(N)` and says so in its title, with a table beside it covering the rest.

Green, amber and red are reserved for state, so no series wears them for identity; multi-series graphs colour
by series name rather than by rank, so a host keeps its colour when a filter changes the series count.

Under each row heading sits a transparent markdown band with one line on what the section answers, because
Grafana's row header alone is a thin grey rule that reads as no boundary.

Temperatures display in Fahrenheit. `node_hwmon_temp_celsius` reports Celsius, so the queries convert with
`* 9 / 5 + 32` and their thresholds move with them; changing only the display unit would label a Celsius
number as Fahrenheit.

Hardware panels are scoped to the machine that owns the hardware. `node_exporter` inside an LXC reports the
node's ZFS pools, NVMe data, sensors and disk statistics, because those read from `/sys` and `/proc` paths
that are not namespaced. Unfiltered, one physical ZFS pool appears as three and one CPU's sensors appear
under seven hostnames.

CPU package temperature joins on the sensor label rather than the chip name:

```promql
node_hwmon_temp_celsius * on (host, chip, sensor) group_left (label)
  node_hwmon_sensor_label{label=~"Package id 0|Tctl"} * 9 / 5 + 32
```

Intel reports the die as `Package id 0` on a `coretemp` chip; AMD reports it as `Tctl`. The previous
`chip=~".*coretemp.*"` filter silently omitted `grey-server`, the fleet's one AMD node.

## History

The 2026-07-13 baseline cleanup installed the three missing Proxmox exporters and removed stale jobs: [Security Monitoring Baseline Cleanup - 2026-07-13](Documentation/Change%20Records/Security%20Monitoring%20Baseline%20Cleanup%20-%202026-07-13.md).

On 2026-07-22 I published Prometheus and Grafana through internal NPM and closed the [Grafana plaintext administrator credential incident](../../Security/Incidents/Grafana/Plaintext%20Administrator%20Credential%20-%202026-07-22.md): [Internal HTTPS Service Onboarding - 2026-07-22](../Nginx%20Proxy%20Manager/Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

The 2026-07-25 expansion took the target set from 7 to 36 and built the overview dashboard. Two follow-ups on 2026-07-26 brought it to 44: enabling UPS collection, then upgrading cAdvisor so the six `overlayfs` hosts report containers. All three are recorded in [Fleet Metrics Expansion and Grafana Overview - 2026-07-25](Documentation/Change%20Records/Fleet%20Metrics%20Expansion%20and%20Grafana%20Overview%20-%202026-07-25.md). Exporter rollout runs from `ansible-01`; the playbooks live in [monitoring-exporters](../Ansible/Source/monitoring-exporters/README.md).

On 2026-07-26 I moved the stack from `security-01` on `grey-server` to CT 104 `monitor-01` on `blue-server`, added the new host's two exporters, and retired the old monitoring files and volumes. The final target set is 46 of 46 `up`: [Monitoring Relocation to monitor-01 - 2026-07-26](Documentation/Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md).
