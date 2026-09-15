# Prometheus

**Created:** 2026-07-13  
**Last updated:** 2026-09-15

On 2026-09-15 I added the private [Uptime dashboard](https://grafana.alphasecunited.com/d/uptime), covering 29 service checks with status bars, a 99.99% sampled-uptime target, and monitoring coverage. I added four missing HTTP probes and a local Cloudflare/Caddy/Coolify collector. All 58 scrape targets are healthy. The [change record](Documentation/Change%20Records/Uptime%20Dashboard%20-%202026-09-15.md) records the measurement limits and verification.

On 2026-09-12 I removed Game 01’s node, cAdvisor and panel targets and its Grafana node dashboard. Prometheus reports 54 targets, all UP; Grafana has no firing or pending Game 01 alert; two resolved cache entries remain. The 24 shared alert rules continue to cover the remaining fleet.

I run Prometheus & Grafana in Docker on CT 104 `monitor-01` at `192.168.73.2`. Prometheus 3.14.0 scrapes 58 targets: `node_exporter` on 17 Linux hosts, cAdvisor on all 8 Docker hosts, What's Up Docker on the 6 Compose hosts, the Proxmox API exporter, `blackbox_exporter` probes of 23 internal service names plus the Discord alert bot's health endpoint, UPS-02 over NUT, and itself. TeamSpeak voice reachability arrives as node_exporter textfile metrics from `alpha-prod-01` rather than a scrape target, so those four public and local UDP checks add series without changing the target count: see [TeamSpeak Reachability Monitoring - 2026-07-28](../Teamspeak%20Hosting/Documentation/Change%20Records/TeamSpeak%20Reachability%20Monitoring%20-%202026-07-28.md).

The [Galaxy Green baseline and monitoring record](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Green%20Baseline%20and%20Monitoring%20-%202026-07-31.md) contains the 2026-07-31 rollout, rollback checks, and live 49-target validation. I use `AG-Proxmox-Nodes` as the destination Network List for `Allow Monitor to Proxmox monitoring`; that dated record explains the membership expansion under its former name.

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
| Uptime dashboard | `https://grafana.alphasecunited.com/d/uptime` |
| Homelab Overview dashboard | `https://grafana.alphasecunited.com/d/homelab-overview` |
| A host's own dashboard | `https://grafana.alphasecunited.com/d/node-<host>`, e.g. `/d/node-grey-server` |
| Live host configuration | `/home/dkadi/monitoring/` on `monitor-01` |
| Versioned configuration | [Configuration/](Configuration/) |
| Versions | Prometheus 3.14.0, Grafana 13.2.1, PeaNUT 6.0.0, blackbox_exporter 0.28.0, cAdvisor 0.60.5, node_exporter 1.9.0 on 15 of the 17 hosts, with `ubuntu-dev` on 1.10.2 and `docker-main` on 1.5.0; all registry-backed monitoring images except the local alert bot follow `:latest` |
| Retention | 15 days |
| Scrape intervals | 15s default; 30s for cAdvisor and NUT, 60s for blackbox probes |

WUD 9 requires authenticated scrapes. Six scrape configurations read separate protected password files under `/etc/prometheus/wud-passwords/` and relabel their series to `job="wud"`. The [2026-09-13 update](../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-13.md) records the migration.

## Containers on monitor-01

Nine containers belong to the host across four Compose projects. `prometheus`, `grafana`, `pve-exporter`, `blackbox-exporter`, `nut-exporter`, and `alert-bot` come from `~/monitoring/docker-compose.yml`. `cadvisor` comes from `/opt/docker/cadvisor`, deployed by the same Ansible playbook that manages the other seven Docker hosts. `wud` comes from `/opt/docker/wud`, deployed by that same project. PeaNUT runs from `/opt/docker/peanut`.

The 2026-08-10 restart exposed a limit in the old policy: Docker held `HasBeenManuallyStopped=true` for Prometheus, so `unless-stopped` skipped it while the other containers returned. I changed Prometheus alone to `restart: always`, started it, and verified both readiness paths, 52 healthy targets, and 20 passing probes. The diagnosis and correction are in [issue 5](Documentation/Troubleshooting/Container%20Remained%20Stopped%20After%20monitor-01%20Restart%20-%202026-08-10.md).

## Scrape Jobs

Jobs are named after the exporter type, with the hostname in a `host` label and a `role` label for dashboard filtering. Before 2026-07-25 there was one job per host, which made `job` double as a hostname and stopped scaling at 14 targets.

| Job | Targets |
|---|---|
| `node` | grey-server, purple-server, blue-server, red-server, green-server, security-01, splunk-siem, edge-01, docker-main, ansible-01, docker-blue, media-01, app-01, alpha-prod-01, docker-network, monitor-01, ubuntu-dev (configured `host` label `ubuntu-dev`) |
| `cadvisor` | all 8 Docker hosts: docker-main, docker-network, docker-blue, media-01, alpha-prod-01, app-01, security-01, monitor-01 |
| `proxmox` | PVE API exporter, covering Galaxy nodes, guests, and storages dynamically |
| `blackbox` | the 23 service names published through NPM, plus `http://alert-bot:8080/health` over the Compose network |
| `nut` | APC Back-UPS RS 1500MS2 UPS-02 on grey-server; UPS-01 left the target set on 2026-08-31 while its data cable remains disconnected |
| `wud` | What's Up Docker `:latest`, verified as 9.0.2 on 2026-09-13, on port 9102 on the 6 Compose hosts: docker-main, docker-network, docker-blue, media-01, alpha-prod-01, monitor-01, scraped every 5 minutes |
| `prometheus` | self-scrape |

The current target set has no retired lab endpoints. The retained node-exporter
targets use the all-interface listener expected by the automation. Prometheus has
its administrative API disabled and all 58 targets up, verified on 2026-09-15. Retired Game 01 samples
remain in historical storage until the 15-day retention expires.

cAdvisor follows `ghcr.io/google/cadvisor:latest`, currently v0.60.5. Its 2026-09-03 reconciliation registered all 69 running containers across the nine Docker hosts. A historical 2026-07-28 query returned 53 named containers across the eight hosts then in scope; `game-01` joined later. cAdvisor covered `docker-main` alone from 2026-07-25 to 2026-07-26, because v0.52.1 registers no containers under Docker 29's `overlayfs` driver and `docker-main` was the only Docker host still on `overlay2`. v0.60.5 handles the containerd snapshotter. See [the troubleshooting record](Documentation/Troubleshooting/cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md).

## Grafana Configuration Is Versioned

Until 2026-07-25 the datasource and both imported dashboards existed only inside the `grafana_data` Docker volume. Removing that volume would have destroyed all of it with nothing in git to rebuild from.

`Configuration/grafana/` now holds the datasource definition, the dashboard providers, all 27 dashboards, and 24 Grafana-managed alert rules, mounted read-only into the container. `allowUiUpdates` is off, so the repository stays authoritative.

The 24 rules sit in six groups. Availability, Capacity, Network and Power and hardware cover host, exporter, service, Proxmox node and named guest availability, container restart loops, filesystem, Proxmox storage, memory, CPU, load and disk capacity, service latency, TLS certificate expiry, UPS state and hardware temperature. Storage health reads the SMART and NVMe textfiles on the five nodes. Updates carries four notify-only rules for pending security updates, other OS updates, a required reboot and a newer container image, fed by the node_exporter textfile collectors on all 17 hosts and What's Up Docker on the six Compose hosts. Only those four Updates rules carry a `class` label, `class: updates`; the other 20 carry no `class` label at all, and the Discord alert bot supplies `infrastructure` as the fallback when the label is absent. Grafana holds all 24 as file-provisioned rules with no evaluation error in the folder `AlphaSec United Alerts`, renamed from `Homelab Alerts` on 2026-09-03; the bot prints the folder name in each message footer. Since 2026-09-02 the root notification policy routes every alert to the contact point `discord-bot`, a webhook into the [Discord Alert Bot](../Discord%20Alert%20Bot/README.md) on the same Compose network, which posts to `#bots` as the Anubis AS bot user and colours the message by class; a child route groups the Updates class by rule name and repeats once a year, so an update is announced once and resolved once. The records are [Grafana Alert Rules - 2026-09-01](Documentation/Change%20Records/Grafana%20Alert%20Rules%20-%202026-09-01.md), [Guest, CPU and Load Alert Rules - 2026-09-02](Documentation/Change%20Records/Guest%20CPU%20and%20Load%20Alert%20Rules%20-%202026-09-02.md) and [Certificate, Drive Health and Update Alert Rules - 2026-09-02](Documentation/Change%20Records/Certificate,%20Drive%20Health%20and%20Update%20Alert%20Rules%20-%202026-09-02.md).

Since 2026-08-27 there are two providers, because seventeen node dashboards in the same folder as the overview would bury it, and because the header dropdowns filter by tag. Their paths must not nest: Grafana's file provider walks its path recursively, so a provider pointing at the parent would claim the node dashboards too and the two would fight over the same files on every scan.

The dashboards carry `"editable": true`, which is not a contradiction with `allowUiUpdates: false`. Provisioning still refuses to persist a browser edit; leaving the flag on keeps panel-edit and Explore reachable so a query can be read without hunting for it in git. To iterate, change the generator and re-run it. A hand edit to a file under `dashboards/` is overwritten by the next build.

The datasource file pins `name: prometheus` and `uid: bfgnkdi47u5tsa` on purpose. Provisioning matches on name, so it adopts the entry that already existed instead of creating a duplicate. The UID was pinned so the two imported dashboards kept resolving; they are gone now, but the pin stays because `homelab-overview.json` references that UID throughout.

## Dashboards

27 dashboards in two Grafana folders, all generated from [Tools/](Tools/README.md) and committed here.

| Folder | Dashboard | UID | Purpose |
|---|---|---|---|
| Homelab | Homelab Overview | `homelab-overview` | Eight health tiles, one table of everything failing a check, the fleet table, and service reachability |
| Homelab | Proxmox · Galaxy Cluster | `proxmox-cluster` | Quorum, the five nodes, every guest, guest I/O, every storage |
| Homelab | Containers | `containers` | Every container across the eight cAdvisor hosts, with restart and OOM tables; the nine-host set held 71 on 2026-09-05 |
| Homelab | Uptime | `uptime` | 29 checks: TeamSpeak through Playit, Cloudflare connector, Caddy and Coolify origins, 23 internal HTTPS names, and the alert bot; status bars, observed uptime, and coverage |
| Homelab | Services & Uptime | `services-uptime` | The 23 published names through NPM plus the alert bot's health endpoint, 24 probes: reachability, latency by request phase, TLS expiry |
| Homelab | Storage & Drive Health | `storage-health` | Capacity and days-to-full first, then NVMe, SATA SMART and ZFS |
| Homelab | Network | `network` | Throughput, errors and drops, TCP state, connection tracking |
| Homelab | Power & UPS | `power-ups` | UPS-02 battery, runtime, load, mains, and status flags; UPS-01 is absent while its data cable remains disconnected |
| Homelab | Monitoring Health | `monitoring-health` | Target health, scrape cost, TSDB growth, the 17 node_exporters |
| Homelab | TeamSpeak | `teamspeak` | ts02 and ts03, with the fault isolated to the server or the path in front of it |
| Nodes | one per host | `node-<host>` | Status, CPU, memory, filesystems, disk, network, then whatever else that host has |

Every header carries two dashboard-link dropdowns filtered by tag: **Homelab** lists the ten and **Nodes** the
seventeen, and both keep the current time range. The fleet table, the guest table, the filesystem and drive
tables and the scrape target list link their host column to that host's dashboard, so each of those is a route
into a node board. A host column is not a link everywhere; several tables, among them the failing-check table
on the overview, print the name on its own.

### One dashboard per host

Seventeen of the 27 are per-host. Each is a real dashboard with its own UID and its own entry in the folder,
not a `$host` filter on a shared one, because a host is a thing you open rather than a variable you set, and
because a filter can only show what is true of every host. A per-host board can show `grey-server`'s ZFS pool
and its UPS, `media-01`'s containers and `blue-server`'s NVMe, and omit each of those sections from the hosts
that lack the capability.

They are generated rather than written for the obvious reason: seventeen hand-kept copies of one layout
diverge the first time one is edited. The layout lives once in `Tools/build_dashboards.py` and the capability
flags in `Tools/inventory.py` decide which sections each host grows.

### Conventions

Panel type follows the data's job: a stat tile for one current value, a bar gauge for a ratio against a limit,
a time series for change over time, a state timeline for up-or-down over time, a table with in-cell bars for
one row per thing, and a table with a written-out empty state for a list that should normally be empty. Above
eight series a time series shows `topk(N)` and says so in its title, with a table beside it covering the rest.

A panel carries its number and nothing else. Since the [2026-09-14 restyle](Documentation/Change%20Records/Dashboard%20Style%20Overhaul%20-%202026-09-14.md)
there are no markdown bands under row headers, no sparklines inside stat tiles, no legend tables under graphs
and no navigation panel; the two header dropdowns are the navigation. Sixty-nine panels keep a short
description drawn from fifteen distinct texts, each saying how a value is computed or why it reads the
way it does; the other 726 have none. A stat tile is one large centred number coloured by its
thresholds, and a count against a fixed total renders as `5 / 5`.

Colour is either state or resource. Tiles, table cells and bar gauges are coloured by their thresholds, so
green, amber and red keep meaning something. A single-series graph wears its resource's tint from `TINT` in
`Tools/dashlib.py`: salmon for compute, blue for memory, orchid for storage, teal for network, yellow for
power, lavender for a count that judges nothing. Multi-series graphs colour by series name rather than by
rank, so a host keeps its colour when a filter changes the series count.

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
