# Fleet Metrics Expansion and Grafana Overview

**Created:** 2026-07-25  
**Last updated:** 2026-07-26

**Implementation date:** 2026-07-25, with UPS and cAdvisor follow-ups on 2026-07-26  
**Status:** Complete  
**Primary owner:** Prometheus infrastructure monitoring  
**Affected systems:** `security-01`, `docker-main`, `docker-network`, `docker-blue`, `media-01`, `alpha-prod-01`, `app-01`, `splunk-siem`, `ansible-01`, UniFi gateway, Grafana

## Scope

I took Prometheus from 7 targets to 36, built a fleet-wide Grafana dashboard on top of it, and put the whole Grafana configuration under version control for the first time. Coverage went from 6 of 15 running hosts to 14, plus reachability probes on all 19 internal service names and UPS groundwork that is blocked on one firewall rule.

## Starting State

Prometheus 3.10.0 and Grafana 12.4.1 ran in Docker Compose on `security-01` at `192.168.72.2` with 7 targets: `node_exporter` on the four Galaxy nodes plus `security-01` and `edge-01`, and the PVE API exporter. Retention was 15 days. There were no rule files, no Alertmanager, and no `remote_write`.

Nine running hosts had no exporter: `docker-main`, `docker-network`, `docker-blue`, `media-01`, `alpha-prod-01`, `ansible-01`, `splunk-siem`, `app-01`, and `kasm-01`. Nothing probed whether any of the 19 proxied services actually answered. Neither APC unit fed Prometheus.

Grafana already held two imported dashboards, Node Exporter Full (`rYdddlPWk`) and Proxmox via Prometheus (`Dp7Cd57Zza`), against a datasource named `prometheus` with UID `bfgnkdi47u5tsa`. Both dashboards and that datasource existed only inside the `grafana_data` Docker volume. The provisioning directories were empty, so `docker volume rm grafana_data` would have destroyed all of it with nothing in git to rebuild from. That was the most dangerous thing I found and it wasn't in the original request.

`app-01` was already serving `node_exporter` on 9100 and wasn't scraped. `Tests/assert_targets.py` listed `192.168.80.10` in `FORBIDDEN_ADDRESSES`, but the [2026-07-13 cleanup record](Security%20Monitoring%20Baseline%20Cleanup%20-%202026-07-13.md) shows it was dropped for being unavailable at the time, not for being unwanted. That exclusion was stale.

## Choices

**One job per exporter type, not one per host.** The old layout used `job_name: 'grey-server'` and friends, so `job` doubled as a hostname. At 14 `node_exporter` targets across five exporter types that stops scaling, so jobs are now `node`, `cadvisor`, `proxmox`, `blackbox`, and `prometheus`, with the hostname in a `host` label and a `role` label for filtering. The cost is a break in any graph spanning the cutover, because `job="grey-server"` series stop where `job="node",host="grey-server"` begins. With 15-day retention that discontinuity ages out by 2026-08-09.

**One exporter version across the fleet.** Debian 13 trixie carries `prometheus-node-exporter` 1.9.0-1+b4, which matches what the four Proxmox nodes already run, so five hosts stayed APT-managed. `docker-main` runs Debian 12 bookworm, where the only candidate is 1.5.0-1+b6, and Rocky Linux 10.2 on `splunk-siem` carries no build in `baseos`, `appstream`, or `extras`. Both got the upstream 1.9.0 binary instead. A 2022 exporter on one host would have meant different metric and label sets under a dashboard that aggregates across hosts, and `grey-server` already runs a hand-installed 1.9.0, so this matches existing practice rather than introducing a new one.

**No EPEL on the SIEM host.** `epel-release` is available to `splunk-siem` from `extras`, and adding a third-party repository to the host that holds the security logs to obtain one binary isn't a trade I wanted. The playbook verifies the download against the release's own `sha256sums.txt`, so no hash is hardcoded and nothing is trusted blind.

**`blackbox_exporter` rather than Uptime Kuma.** Uptime Kuma would have meant a second monitoring system with its own database, UI, credential, and NPM entry, and its `/metrics` endpoint requires basic auth, which would put a secret in a versioned file. blackbox is one container reading a YAML file I keep in the repository, with targets living in `prometheus.yml` under the procedure the runbook already documents. It also reports `probe_ssl_earliest_cert_expiry`, so the wildcard certificate expiring 2026-10-08 is now tracked without my remembering to check.

**Probe through NPM, not at the backends.** Probing `https://immich.<domain>/` tests local DNS, the proxy, the certificate, and the backend in one request, which is the path a person actually uses. Probing `192.168.40.35:2283` would have tested a quarter of that.

**Accepting 401 and 302 as reachable.** Several of these services answer a redirect or an auth challenge at the root path when unauthenticated. Treating that as an outage would have made the panel lie, so `valid_status_codes` covers 200, 204, 301, 302, 303, 307, 308, 401, and 403. The question the panel answers is whether the service responded, not whether it liked the request.

**`prometheus-nut-exporter` rather than scraping PeaNUT.** PeaNUT does expose `/api/v1/metrics`, and Prometheus could authenticate to it with `basic_auth: password_file:` to keep the secret off git. Two things decided against it. `upsd.users` is empty on both NUT hosts and anonymous reads work, so the direct path needs no credential at all. And scraping PeaNUT would make UPS history depend on `docker-main` staying up, which is precisely what a power event threatens.

**File provisioning for Grafana.** The dashboard JSON and datasource YAML live in `Configuration/grafana/` and mount read-only into the container. `allowUiUpdates: false` keeps the repository authoritative; iterating in the browser means Save As to a scratch copy, then folding the change back into the versioned JSON. The datasource file pins `name: prometheus` and `uid: bfgnkdi47u5tsa` deliberately, so provisioning adopts the existing entry in place instead of creating a duplicate and orphaning the two imported dashboards.

**Ansible, not 9 SSH sessions.** The `ansible` account with `NOPASSWD` sudo already reaches these hosts from `ansible-01`, so the rollout is a new project at `Source/monitoring-exporters/` alongside `fleet-updates`, with its own inventory, two playbooks, and a structural validator.

## Actions and Observed Results

### 1. Backups

Dated copies of `docker-compose.yml`, `prometheus.yml`, and `pve.yml` under `/home/dkadi/monitoring/`, plus a 3,395,584-byte copy of `grafana.db` read out of the running container into `~/monitoring/backups/`. I confirmed the copy starts with the `SQLite format 3` magic and matches the live file's size before touching anything.

### 2. node_exporter on seven hosts

The first run failed on `docker-main` with `no available installation candidate for prometheus-node-exporter=1.9.0-1+b4`, which is how I found the bookworm-versus-trixie split. The playbook now reads the APT candidate and picks the install method from it rather than from the package manager, so a host that can't reach 1.9.0 through APT falls through to the pinned upstream release.

All seven reported 1.9.0 afterward:

| Host | OS | Method |
|---|---|---|
| `docker-main` | Debian 12.14 | binary |
| `docker-network` | Debian 13.1 | apt |
| `docker-blue` | Debian 13.5 | apt |
| `media-01` | Debian 13.6 | apt |
| `alpha-prod-01` | Debian 13.5 | apt |
| `ansible-01` | Debian 13.5 | apt |
| `splunk-siem` | Rocky 10.2 | binary |

A second run reported `changed=0` on every host. The play asserts the version the exporter actually reports rather than trusting the package manager, so a silent version drift fails the run.

I deliberately left the `prometheus-node-exporter-collectors` package off these hosts. Its `smartmon` script finds no block devices inside an LXC or behind a virtio disk, which would pin `node_textfile_scrape_error` at 1 and report a fault that isn't real.

### 3. cAdvisor, and where it doesn't work

The guard caught a genuine conflict on the first run: `docker-network` already had the NetBird server on 8081. I moved the fleet to 9101, which is free on all seven hosts and sits next to `node_exporter`.

Deployment then succeeded everywhere, and six of the seven reported no containers. `docker-main` is the only Docker host still on the `overlay2` storage driver; the other six use Docker 29's `overlayfs` driver, where cAdvisor v0.52.1 can't resolve a container's read-write layer ID and abandons registration entirely. I removed it from those six rather than leave 3,600 series of root-cgroup data and a log line every minute. That held for one day; the follow-up below fixed it properly. The full diagnosis is in [cAdvisor Registers No Containers Under the Docker 29 overlayfs Driver](../Troubleshooting/cAdvisor%20Registers%20No%20Containers%20Under%20the%20Docker%2029%20overlayfs%20Driver%20-%202026-07-25.md).

Container health on the touched hosts was unaffected: `docker-main` 14 containers, `media-01` 9, `alpha-prod-01` 7, `docker-network` 4, `docker-blue` 3, zero unhealthy and zero restarting throughout. Coolify on `app-01` kept answering 302 on 8000.

### 4. Firewall

Four new UniFi policies, each scoped to `192.168.72.2` as the only source, all with automatic respond-policy generation enabled:

| Policy | Destination | Ports |
|---|---|---|
| Allow Security to Personal-A monitoring | `.40.35`, `.40.36`, `.40.39`, `.40.42` | 9100, 9101 |
| Allow Security to A-Servers monitoring | `.80.10`, `.80.118` | 9100, 9101 |
| Allow Security to A-Access monitoring | `.85.2` | 9100, 9101, 443 |
| Allow Security to Proxmox NUT | `.70.10`, `.70.13` | 3493 |

`splunk-siem` needed no policy because it shares Security-A with Prometheus. All eight cross-zone targets answered 200 on 9100 immediately afterward, and 443 to NPM confirmed working through the hostname rather than the bare IP, which returns nothing because NPM matches on SNI.

The NUT policy alone didn't open the path. The Proxmox cluster firewall at `/etc/pve/firewall/cluster.fw` is a second enforcement layer, and it permits `192.168.40.35` to 3493 for PeaNUT but has no equivalent rule for `192.168.72.2`. That edit is the one step I did not complete; see Remaining Work.

### 5. security-01 stack

`blackbox-exporter` v0.27.0 on 9115 and `hon95/prometheus-nut-exporter:1` on 9995 joined the Compose project, and Grafana was recreated with two read-only provisioning mounts. The versioned Compose file is new: the live file had never been in the repository.

Grafana logged an error on start for a missing `plugins` and `alerting` provisioning directory, because mounting my `provisioning` directory over the image's replaced the empty subdirectories it ships. I added placeholder files for all four subdirectories. The restart afterward logged no errors.

### 6. Prometheus configuration

I wrote the new configuration into the existing `prometheus.yml` inode with `cat candidate > prometheus.yml` rather than replacing the file. The 2026-07-13 change lost a reload because a single-file bind mount stayed attached to the old inode; preserving the inode removes that failure mode instead of working around it afterward. `promtool check config` passed against the candidate inside the container before it went live.

## Resulting Configuration

36 targets across 5 jobs, all `up`:

| Job | Targets | Interval |
|---|---|---|
| `node` | 14 hosts | 15s |
| `cadvisor` | `docker-main` only | 30s |
| `proxmox` | PVE API exporter | 15s |
| `blackbox` | 19 service names through NPM | 60s |
| `prometheus` | self-scrape | 15s |

The intervals aren't uniform on purpose. Uptime doesn't need 15-second resolution, and 60s holds the probe load on NPM to 19 requests a minute instead of 76.

The Homelab Overview dashboard carries 27 panels in 8 rows at `/d/homelab-overview`, in a `Homelab` folder, with links out to the two existing dashboards for per-host and per-guest drill-down. It doesn't duplicate them: it answers "is anything wrong across the whole lab" and hands off for detail.

Two findings from query validation shaped the panels. `node_exporter` inside an LXC reports the *host's* ZFS pools, NVMe SMART data, and disk statistics, because those come from `/sys` and `/proc` paths that aren't namespaced. Unfiltered, `node_zfs_zpool_state` returned 4 hosts for a single physical pool and the CPU temperature panel returned 13 series for 4 CPUs. Every hardware panel is scoped to `role="hypervisor"`, which brings those to 1 and 4. The nodes also expose 40-plus `fwbr`, `fwln`, `fwpr`, `veth`, and `tap` interfaces each, so the throughput panel is restricted to real uplinks.

I left several things off deliberately. A failed-collector panel would sit permanently red, because 9 collectors fail on every node by design, including `conntrack`, `infiniband`, `nfs`, `rapl`, and `tapestats`. `pve_not_backed_up_info` reads 1 for all 21 guests because the guest-backup target was waived, so a panel for it would be a permanently red number reporting a decision rather than a fault. `pve_ha_state` emits 11 series per guest across 21 guests, all zero except `lxc/107` and `lxc/108`. The `systemd` collector is present on `red-server`, `blue-server`, and `purple-server` only, at over 1,000 units each, and a fleet panel built on three of fourteen hosts would mislead rather than inform.

## Verification

`promtool check config` passed. The rewritten [assert_targets.py](../../Tests/assert_targets.py) exits 0 and reports 36 expected targets present and all UP, 17 scraped exporters plus 19 blackbox services, with stale addresses absent. It now keys on scrape URL and checks the `job` and `host` labels, because a target is no longer identified by its job label alone.

A new [assert_dashboard_queries.py](../../Tests/assert_dashboard_queries.py) walks the dashboard JSON, substitutes the Grafana variables, and runs all 40 expressions against the Prometheus API. 39 returned data; 1 returned nothing and is on an explicit allow-list, because an empty container-restart table means nothing restarted. A dashboard can load cleanly and still show empty panels, which reads as "nothing wrong" and is worse than a visible break.

I ran 8 representative queries a second time through Grafana's own `/api/ds/query` endpoint rather than against Prometheus directly, which tests the datasource proxy the panels actually use. All returned frames.

The Grafana API confirms `provisioned: true` for `homelab-overview` in the `Homelab` folder, and exactly 1 datasource, still UID `bfgnkdi47u5tsa`, now `readOnly: true`. No duplicate was created and the two imported dashboards still resolve. Grafana logs no errors after the placeholder fix.

Rendering is the one thing I could not verify. Grafana has no image-renderer plugin, so there is no server-side screenshot, and I don't log into the UI. The queries, the provisioning state, and the datasource path are all confirmed; what the panels look like is worth a look in the browser.

## Rollback Points

On `security-01`, all suffixed `.bak.fleet-metrics-expansion-20260725`: `docker-compose.yml`, `prometheus.yml`, and `pve.yml` in `~/monitoring/`, plus `grafana.db` in `~/monitoring/backups/`. Restoring the Grafana database reverts the dashboard and datasource to their pre-change state.

Removing the two provisioning mounts from the Compose file and recreating Grafana reverts to whatever the volume holds. Exporters come off with `apt remove prometheus-node-exporter` on the APT hosts, or by disabling `node_exporter.service` and deleting `/usr/local/bin/node_exporter` on the two binary hosts. cAdvisor comes off with `-e cadvisor_state=absent`. Each of the four UniFi policies deletes independently.

## 2026-07-26 Follow-Up: UPS Metrics

The NUT job was left disabled on 2026-07-25 because the Proxmox cluster firewall dropped the path even with the UniFi policy in place. I closed that the next day.

Two `IN ACCEPT` lines went into the `pve_mgmt` group of `/etc/pve/firewall/cluster.fw`, inserted directly after the existing PeaNUT rules so they sit above the trailing `IN DROP` entries, which are order-sensitive. I built the candidate with `awk` into `/root`, checked it before installing rather than after (51 lines against 49, four references to 3493, both `DROP` rules and all five IPSets intact), then copied it over the pmxcfs path. `pve-firewall compile` passed with four compiled 3493 rules and SSH and GUI listeners stayed up. `cluster.fw` lives on pmxcfs, so it replicated to all four nodes without touching them individually.

TCP 3493 to both `192.168.70.13` and `192.168.70.10` went from BLOCKED to OPEN, and the exporter returned HTTP 200 for both targets. I enabled the `nut` job through the runbook procedure, which brought the target count to 38, all `up`.

First readings, which also confirm the exporter's units:

| Metric | ups01 (red-server) | ups02 (grey-server) |
|---|---|---|
| `nut_ups_status{status="OL"}` | 1 | 1 |
| `nut_battery_charge` | 1.0 | 1.0 |
| `nut_load` | 0.27 | 0.16 |
| `nut_battery_runtime_seconds` | 1,671 | 3,009 |
| `nut_input_volts` | 122 | 126 |
| `nut_real_power_nominal_watts` | 900 | 900 |

`nut_battery_charge` and `nut_load` are ratios rather than percentages, so the panels multiply by 100. The load panel shows watts instead, computed as `nut_load * nut_real_power_nominal_watts`, because 900 W is the figure that decides whether another host fits on a unit.

A Power row went onto the dashboard: mains status per unit, battery charge, load in watts, runtime remaining, and history for input voltage and load. Input voltage history is the reason this exporter earns its place over PeaNUT, which shows live values only and so cannot tell me about a sag that happened overnight. That took the dashboard to 33 panels across 9 rows, with the query assertion covering 46 expressions and 45 returning data.

`ups01` reads 27% load and 1,671 seconds of runtime, against the 58% and 675 seconds recorded on 2026-07-22. The load moved because guests moved; the runtime figure tracks load rather than being a fixed property of the battery.

## 2026-07-26 Follow-Up: Fahrenheit and Layout

Temperatures now read in Fahrenheit. The conversion happens in the query, `* 9 / 5 + 32`, with the thresholds moved to match: 70C became 158F, 80C became 176F, 90C became 194F. Switching only the display unit would have printed a Celsius number labelled Fahrenheit, which is worse than leaving it in Celsius. Checked against the values the same panels showed before: grey-server's 48.9C reads 120.0F.

I also regrouped the dashboard. The first cut had rows that mixed concerns: "Host vitals" carried CPU, memory and a filesystem panel, and "Node hardware health" carried temperatures next to drive health, so finding anything meant knowing which of two rows it happened to live in. It is now one concern per row across eleven rows: fleet status, services, guests, CPU, memory, storage capacity, drive health, power, containers, network, and the monitoring stack itself. Temperature sits with the thing it measures rather than in a hardware bucket.

Panels also got room. The old layout packed six stats across at `w=4` and split a nineteen-row table into a fourteen-column panel; it now runs mostly two-across at half width, tables get full width, and panel heights come from how many series each one actually draws instead of a uniform guess. Rows collapse on click for anyone who wants it shorter.

Grafana's only native divider is the row header, a thin grey bar with a title on it, and it reads as almost nothing between two dense panels. So each row heading is followed by a transparent markdown panel holding one line about what that section answers, then a horizontal rule. That gives the eye a boundary to land on and makes each section explain itself, at three grid rows of cost per section. Text panels carry no `targets`, so the query assertion walks straight past them.

The dashboard now stands at 34 data panels plus 11 separator bands over 213 grid rows. Longer to scroll, easier to read.

One rename for clarity, now that CPU load and UPS load appear on the same page: the power panels are "UPS load" and "UPS load over time" rather than "Load" and "Load over time".

The query assertion was re-run after every change in this section. Final state: 47 queries, 46 returning data, one allowed empty (the container restart table, which is correct when nothing has restarted), none erroring, and no `level=error` lines in the Grafana log.

## 2026-07-26 Follow-Up: Per-Container Metrics On All Seven Docker Hosts

The 2026-07-25 work left cAdvisor on `docker-main` alone, covering 14 containers of roughly 46, because v0.52.1 registers none under Docker 29's `overlayfs` driver. I recorded that as a limitation with no fix available. It had a fix available.

My version check was wrong. I probed `v0.53.0`, `v0.54.0` and `v0.55.0` on `gcr.io/cadvisor/cadvisor`, got no manifest for any of them, and read that as "v0.52.1 is current". Resolving `latest` instead:

```
gcr.io/cadvisor/cadvisor:latest   v0.55.1
ghcr.io/google/cadvisor:latest    v0.60.5
```

Eight releases past the one I deployed, on a registry I never checked. v0.60.5 handles the containerd snapshotter.

I tested it on `security-01` first, since that host runs `overlayfs` and carries the monitoring stack rather than anyone's workload: 6 named containers of 6 running, zero `read-write layer` errors, 959 series. Then rolled it through the playbook to all seven hosts.

| Host | Docker | Driver | Registered |
|---|---|---|---|
| docker-main | 29.6.1 | overlay2 | 14 of 14 |
| media-01 | 29.6.2 | overlayfs | 9 of 9 |
| alpha-prod-01 | 29.6.1 | overlayfs | 7 of 7 |
| app-01 | 29.6.1 | overlayfs | 7 of 7 |
| security-01 | 29.6.1 | overlayfs | 6 of 6 |
| docker-network | 29.6.1 | overlayfs | 4 of 4 |
| docker-blue | 29.5.3 | overlayfs | 3 of 3 |

`ok=14 changed=3` per host, nothing failed, nothing unreachable. No firewall work was needed: the 2026-07-25 policies already permitted 9101 from `192.168.72.2` into every zone involved, and all seven answered 200 from `security-01` on the first try.

The `cadvisor` scrape job went from 1 target to 7, taking Prometheus from 38 to 44, all `up`. `count by (host) (container_last_seen{name!=""})` reports 50 containers, seven of which are the cAdvisor containers.

Three things changed beyond the image tag:

The container panels went fleet-wide and now group by `host` as well as `name`. A container name is only unique within a host, so aggregating on name alone would have merged two hosts running the same image into one series and shown a number that belongs to neither. The row is titled "Containers" instead of "Containers on docker-main", and the descriptions no longer carry the scope warning. All 47 dashboard queries return data.

The playbook stopped asserting on the storage driver. That pre-flight check refused to install unless the driver was `overlay2`, which encoded one cause and would have blocked this fix. It now counts what cAdvisor registered after installing and fails when a host with running containers reports none, which catches the same failure without pretending to know why it happened.

The `cadvisor_incompatible` inventory group is gone, and the validator fails if it comes back. Six hosts listed as permanently incompatible were nothing of the kind.

## 2026-07-26 Follow-Up: Deleted The Two Imported Dashboards

Grafana now serves one dashboard. I deleted Node Exporter Full (`rYdddlPWk`, 39 panels) and Proxmox via Prometheus (`Dp7Cd57Zza`, 14 panels), both community dashboards imported from grafana.com before this project started and both `provisioned: false`, meaning they lived only in `grafana.db`. The search API returns a single dashboard now, `homelab-overview` in the `Homelab` folder, and the datasource is untouched: one entry, UID `bfgnkdi47u5tsa`, `readOnly: true`.

They were the last unversioned thing Grafana was showing, so the repository is now the complete record of it.

I kept no export. Deliberate, and the trade is worth stating: both are public dashboards recoverable by ID from grafana.com in about a minute, so the only thing lost is the datasource binding and variable selections a fresh import would ask for again. The 2026-07-25 `grafana.db` tarball also predates the deletion if a real restore is ever wanted.

The two entries in the overview's `links` block pointed at those UIDs and would have rendered as buttons landing on "Dashboard not found", so both came out. The block is now empty.

**That left a real gap**, closed in the next section. Homelab Overview aggregates by host on purpose and carried no per-host CPU, disk, network, or filesystem detail, because Node Exporter Full covered that and duplicating it would have been the noise the whole dashboard was built to avoid.

## 2026-07-26 Follow-Up: Per-Host Detail, Built Rather Than Imported

Deleting Node Exporter Full cost the per-host drill-down, so I rebuilt it in the versioned dashboard. Re-importing was the other option and it was the worse one: 39 panels of somebody else's design, most of it detail this dashboard exists to filter out, and unversioned again the moment it landed.

It sits in a **collapsed** row named `Per-host detail`, driven by a new `$host` variable. Collapsed matters: the row costs one grid line until someone expands it, so the overview stays a fleet summary and the drill-down is one click away rather than 40 panels of scrolling.

Eight panels, each earning its place by showing something the fleet rows flatten:

| Panel | What the fleet view cannot tell you |
|---|---|
| CPU by mode | The fleet CPU panel gives one busy percentage. This splits it, so `iowait` versus `steal` versus real work is visible |
| Load average against core count | Load only means something next to core count, so the count is drawn as a threshold series |
| Memory breakdown | Cached and buffers are reclaimable; a host that looks full is often fine |
| Swap in use | Sustained swap is real pressure and appears nowhere else |
| Every filesystem on this host | The fleet Storage panel shows root only. A full `/var/lib/docker` on an otherwise healthy host was invisible |
| Network per interface | Fleet Network shows uplinks only, transmit drawn negative for direction |
| Disk throughput by device | Per-device read and write |
| Host facts | Kernel, architecture, core count, uptime, in one table |

ZFS, SMART, and NVMe stay out, because they already sit under Drive health scoped to `role="hypervisor"` for the LXC bleed-through reason recorded above. The disk throughput panel is the one that had to be handled rather than excluded: `/proc/diskstats` is not namespaced either, so on an LXC guest it reports the hypervisor's physical devices. Its description says exactly that instead of pretending otherwise.

Every expression matches with `host=~"$host"`, and `assert_dashboard_queries.py` resolves `$host` to `.*`, so the row is tested against all 14 hosts at once rather than whichever one happened to be selected. 65 queries now, 64 returning data, one allowed empty.

## Remaining Work

**`kasm-01` has no exporter.** It sits outside the Ansible inventory and its move to `purple-server` is still an open plan, so its addressing may change. Adding it now would mean redoing the inventory entry and the firewall scope afterward.

**Per-container metrics cover 14 of roughly 46 containers.** Tracked in the [platform TODO](../TODO.md) against the cAdvisor troubleshooting record.

**UniFi gateway, switch, and access-point metrics are not collected.** Skipped by decision, since `unpoller` needs a read-only UniFi local account and that credential deserves its own change.
