# Dashboard Rebuild and Per-Node Boards

**Created:** 2026-08-27  
**Last updated:** 2026-08-27

**Date:** 2026-08-27  
**Scope:** Replace the two hand-maintained dashboards with a generated set of 27: nine organised by concern, and one per host.

## What was there

Two dashboards. `Homelab Overview` carried 34 visible panels across 11 concern rows plus a collapsed
`Per-host detail` row driven by a `$host` variable, and `TeamSpeak` carried 15. Both were hand-written JSON.

Three things were wrong with that.

**The overview was doing four jobs.** It was the health summary, the service list, the guest inventory, the
storage report, the power panel and the container view, in one 3,757-line file that scrolled past 200 grid
rows. Nothing was hard to find because it was hidden; it was hard to find because everything was on one page.

**Per-host detail was one dashboard wearing eighteen hats.** The `$host` variable worked, but a host is a
thing you open, not a filter you set, and the collapsed row could only show what was true of every host at
once. It could not show grey-server's ZFS pool, or media-01's containers, or red-server's UPS, because those
are true of some hosts and not others.

**`TeamSpeak` had been built for one server and now had two.** `ts01` was retired on 2026-08-09 and `ts03`
added, and every stat panel queried a bare metric with no aggregation, so each one silently rendered two
values side by side. It also led with `Public address reachable`, which is exactly the panel that lied for
17 days while the collector could not resolve DNS. See
[Collector DNS Failure After a Boot Race](../../../Teamspeak%20Hosting/Documentation/Change%20Records/Collector%20DNS%20Failure%20After%20a%20Boot%20Race%20-%202026-08-27.md).

## What there is now

27 dashboards in two Grafana folders.

| Folder | Dashboard | What it answers |
|---|---|---|
| Homelab | [Homelab Overview](https://grafana.alphasecunited.com/d/homelab-overview) | Is anything wrong, and where do I go next |
| Homelab | [Proxmox · Galaxy Cluster](https://grafana.alphasecunited.com/d/proxmox-cluster) | Quorum, five nodes, every guest, every storage |
| Homelab | [Containers](https://grafana.alphasecunited.com/d/containers) | 56 containers across nine Docker hosts |
| Homelab | [Services & Uptime](https://grafana.alphasecunited.com/d/services-uptime) | 19 names through NPM, latency phases, TLS expiry |
| Homelab | [Storage & Drive Health](https://grafana.alphasecunited.com/d/storage-health) | Capacity, then NVMe, SMART and ZFS underneath it |
| Homelab | [Network](https://grafana.alphasecunited.com/d/network) | Throughput, errors, TCP state, conntrack |
| Homelab | [Power & UPS](https://grafana.alphasecunited.com/d/power-ups) | Both APC units |
| Homelab | [Monitoring Health](https://grafana.alphasecunited.com/d/monitoring-health) | Does the monitoring itself work |
| Homelab | [TeamSpeak](https://grafana.alphasecunited.com/d/teamspeak) | ts02 and ts03, fault isolated |
| Nodes | `node-<host>` × 18 | One host, everything about it |

Navigation is two dashboard-link dropdowns in every header, filtered by tag: **Homelab** lists the nine,
**Nodes** lists the eighteen. Both keep the current time range when you jump. Any table with a hostname in it
links that column to that host's dashboard, so the overview's Fleet table, the Proxmox guest table, the
storage tables and the target list are all ways into a node board.

## Why generated rather than written

Eighteen hand-maintained copies of the same layout diverge the first time one of them is edited. So the
per-node layout exists once, in `Tools/build_dashboards.py`, and each host's capability flags in
`Tools/inventory.py` decide which sections it grows. `grey-server` gets a ZFS section and `blue-server` does
not. `media-01` gets a container section, `edge-01` does not. The five nodes get a Guests section, and only
`red-server` and `grey-server` get a Power section.

That is also what makes the set look like one thing. Line weight, legend shape, threshold colours, row
banding and column formatting come from `Tools/dashlib.py`, so 80% amber means the same thing on all 27.

The generated JSON is committed. The repository is still the complete record of what Grafana shows; the
generator is how the record is produced, not a substitute for it.

## Choosing the panel type

The dashboards answer, per panel, the question of what form the data's job wants:

| The data's job | Form used |
|---|---|
| One current value | stat tile, with a sparkline where the trend adds something |
| A ratio against a known limit | bar gauge: filesystem used, battery charge, certificate days |
| Change over time, up to 8 series | time series |
| Change over time, more than 8 | time series of `topk(N)`, with a table beside it that covers all of them |
| Up or down over time | state timeline: service reachability, UPS status flags |
| One row per thing, many columns | table, with the magnitude column drawn as an in-cell bar |
| A list that should be empty | table, with the empty state written out as a sentence |

Two colour rules hold throughout. Green, amber and red are reserved for state, so no series wears them for
identity. Multi-series graphs colour by series name rather than by rank, so a host keeps its colour when a
filter changes how many series are drawn.

`topk` is never silent. Every panel that shows a top N says so in its title and points at the table that
covers the rest, because a chart that quietly drops thirteen hosts reads as a chart of the whole fleet.

## Panels that fix something that was wrong

**CPU package temperature missed grey-server.** The old panel matched `chip=~".*coretemp.*"`. `coretemp` is
Intel. `grey-server` is AMD and reports its die as `Tctl` on a k10temp chip, so the one node with 16 threads
and the ZFS pool was absent from the fleet temperature panel and nothing said so. Every temperature query now
joins on the sensor label instead:

```promql
node_hwmon_temp_celsius * on (host, chip, sensor) group_left (label)
  node_hwmon_sensor_label{label=~"Package id 0|Tctl"} * 9 / 5 + 32
```

All five nodes now report. Per-core panels match `Core .*|Tccd.*` for the same reason.

**SMART reported two false failures.** `smartmon_device_smart_healthy == 0` was true for `alpha-prod-01` and
`ubuntu-dev`, both of which expose a `QEMU HARDDISK` with `smart_available = 0`. The self-assessment is
absent, not failed. Every SMART check is now gated on availability:

```promql
smartmon_device_smart_healthy == 0 and on (host, disk) smartmon_device_smart_available == 1
```

NVMe health is not lost to that gate; it arrives through `nvme_critical_warning` and the spare-capacity check.

**Drives disagree about which attribute carries temperature.** The Samsung SSD in `purple-server` reports
only `airflow_temperature_cel`; the three spinners report `temperature_celsius`. The tables read
`(temperature_celsius or airflow_temperature_cel)` so all four show a temperature.

**Nothing led with DNS.** `teamspeak_dns_srv_up` had been 0 since 2026-08-10 with no panel showing it. It is
now a top-row tile called `Name resolution` beside `Public address` and `Local voice`, and a `Relay
endpoints` table renders the collector's `unresolved:0` as `unresolved: DNS failed` in red.

## The panel worth having

`Anything failing a health check` on the overview is one table running twelve checks, unioned with `or`, each
arm a filtered comparison that returns nothing when it passes. Scrape targets down, services unreachable,
certificates inside 21 days, ZFS not online, NVMe critical warnings or spare under 10%, filesystems over 90%
or read-only, a UPS on battery, a failed SMART self-assessment, and either TeamSpeak fault.

A healthy fleet returns zero rows and the panel says *All clear: nothing is failing a health check.* Those
are also exactly the conditions the still-open alerting item would fire on, so when Alertmanager arrives the
rules are already written down here.

## Verification

```
$ python3 Tools/build_dashboards.py
27 dashboards
$ python3 Tests/assert_dashboard_layout.py Configuration/grafana/dashboards
Checked 27 dashboards, 27 unique uids
No overlaps, nothing outside the 24-column grid, one datasource throughout.
$ python3 Tests/assert_dashboard_queries.py Configuration/grafana/dashboards http://192.168.73.2:9090
27 dashboards, 1394 queries: 1389 returned data, 5 allowed empty, 0 unexpectedly empty, 0 errored
```

The five allowed-empty are correct-when-empty panels: the container restart and OOM tables, the network error
table, the failed-unit and pending-update tables, and `Guests on purple-server`, which has no guests today.
The allowed list is generated by the builder into `Tests/allow-empty.json` rather than hand-kept, so a panel
built to be empty registers itself.

After deploying and restarting Grafana, all 27 were present in the two folders with no provisioning errors in
the log, and the stored specs still carried the table transformations, field overrides, data links and header
link dropdowns, the parts Grafana's schema migration was most likely to alter.

## Two tests changed

`assert_dashboard_queries.py` now takes a directory as well as a file, walks it recursively, reads the
allowed-empty list from `allow-empty.json`, and knows the five new template variables. One run covers all 27.

`assert_dashboard_layout.py` is new. Grafana does not reject a dashboard whose panels overlap or run past
column 24: it silently reflows them, so the file in git and the thing on screen stop being the same document
and no error says so. Since the panels are placed by a generator, the check is on the generator.

## Rollback

`~/monitoring/grafana-dashboards-backup-2026-08-27.tgz` on `monitor-01` holds the previous `dashboards/` and
`provisioning/dashboards/` directories. Restore both and restart Grafana. The two retired dashboards are also
in git history at the commit before this one.

Provisioning changes need a Grafana restart, not just a file copy, because the provider YAML is read at
startup. Dashboard JSON alone still needs neither: Grafana re-reads both directories every 30 seconds.
