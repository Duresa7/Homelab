# Dashboard Style Overhaul

**Created:** 2026-09-14  
**Last updated:** 2026-09-14

**Date:** 2026-09-14  
**Scope:** Restyle all 26 dashboards from the generator so a panel carries its number and nothing else, and remove the explanatory prose.

## Why

The dashboards had accumulated a layer of writing that sat between me and the numbers. Under every row heading was a transparent markdown band explaining what the section answered. Most panels carried a hover description, and many of those restated the title or told me where to look next. 104 of the 271 stat tiles drew a sparkline behind the value, 179 of the 372 time series carried a legend table of last and max, and the overview ended in a ten-link navigation table duplicating the header dropdowns.

I removed the same thing once before, on the overview alone, in commit `f45429f`: *the hover text restated what the panel titles already said*. This applies that decision to the whole set and to the generator, so it stays removed.

## What changed

These counts cover all 26 dashboards.

| | Before | After |
|---|---|---|
| Markdown text panels | 181 | 0 |
| Panels carrying a description | 438 | 62, across 14 distinct texts |
| Stat tiles with a sparkline | 104 | 0 |
| Stat tiles on a coloured background | 35 | 0 |
| Time series with a legend table | 179 | 0 |
| Panels, excluding rows and text | 786 | 786 |
| Queries | 1,327 | 1,327 |

No data panel, query or dashboard was added or removed. What left was the 181 text panels and the one row that held the navigation table, so 1,148 panel objects became 966 and the 967 non-row count became 786.

**Rows are a rule, not a place to write.** `Grid.section()` now takes a title and an optional `collapsed` flag, with no prose parameter, and `dashlib.text()` is gone, so there is no constructor that puts prose on a dashboard. `collapsed_section()` lost its blurb parameter too.

**Fifteen texts survive, on 69 panels.** Each says how a value is computed, or why a number reads the way it does, rather than what to conclude. Nine came through the restyle; the two review passes below added seven and merged two into one.

- Memory used, against `MemAvailable`, so page cache counts as free
- Load per core, the one-minute average divided by core count
- CPU by mode, normalised to one core so the stack tops out at 100%
- Container CPU, where 100% is one full core
- 24-hour availability, which ignores the time picker
- Draw, the load share times the 900 W nominal rating as the UPS estimates it
- Guests with no backup, meaning no vzdump archive on any storage Proxmox can see
- Storage used, where a shared storage appears once per node that mounts it
- UPS status flags, expanding OL, OB, LB, CHRG and RB
- Services reachable and Reachable, one text on both tiles, naming the published names and the excluded bot probe
- Interfaces down, naming the parked wireless, spare and tunnel devices that sit there permanently
- Guests stopped, noting that templates and spares are stopped on purpose
- ZFS pools online, noting that the metric emits one series per pool state, not per dataset
- Errors and drops, naming the steady-state receive drops on the five hypervisor NICs
- Node disk throughput on an LXC board, saying the block devices are the hypervisor's

**Stat tiles are one large centred number.** `justifyMode` is `center`, `graphMode` is `none`, and the tile is coloured by its thresholds through `colorMode: value` rather than by flooding the panel background. A tile that reports a fact rather than judging one, such as uptime or core count, has no state-dependent cutoffs: it takes the new `INFO` default, a single neutral-lavender base step. Default tile height went from 4 to 5 so the number has room.

A count against a fixed total now renders as `5 / 5`. `dashlib.out_of(n)` returns the suffix unit, and it is on six tiles: Proxmox nodes online and Services reachable on the overview, Nodes online on Proxmox, Docker hosts reporting on Containers, Reachable on Services, and ZFS pools online on Storage. Two of those six denominators were wrong when first written, and two more tiles paired a correct denominator with a query that counted something else. The review section below corrects all four.

**Colour means one of two things now.** Tiles, table cells and bar gauges are coloured by their thresholds, so green, amber and red still mean state. A single-series graph takes a fixed tint from the new `TINT` map, six hues keyed by resource: salmon for compute, blue for memory, orchid for storage, teal for network, yellow for power, lavender for a count that judges nothing. None of the six is a threshold colour, so a tinted line is never read as a state. Graphs with several series keep `palette-classic-by-name`.

A single series also gets a 14% gradient fill under the line. "Single" means one query with no `{{...}}` in its legend, because `topk(5, ...)` labelled `{{host}}` is one query and five lines; those stay unfilled and coloured by name.

**Titles are shorter and consistent.** A top-N panel now reads `CPU · top 5`, where it used to spell out that it showed the five busiest hosts. Empty-state sentences became labels, so the health-check table reads `All clear` instead of a full sentence saying nothing was failing a check.

**Tile rows are wider.** The six-tile rows on Proxmox, Containers, Services, Storage, Network, Power and Monitoring went from `w=4` to `w=8`, so they lay out as two rows of three rather than one row of six, and each tile is twice as wide.

## Verification

The generator, the layout assertion and the live query assertion all run from `Platforms/Prometheus`:

```
$ python3 Tools/build_dashboards.py
26 dashboards
  homelab-overview             Homelab Overview                    13 panels
  proxmox-cluster              Proxmox · Galaxy Cluster            18 panels
  containers                   Containers                          16 panels
  services-uptime              Services & Uptime                   12 panels
  storage-health               Storage & Drive Health              17 panels
  network                      Network                             15 panels
  power-ups                    Power & UPS                         17 panels
  monitoring-health            Monitoring Health                   18 panels
  teamspeak                    TeamSpeak                           17 panels
  node-*                       one per host                        44 panels (17 files)
39 panel titles registered as allowed-empty

$ python3 Tests/assert_dashboard_layout.py Configuration/grafana/dashboards
Checked 26 dashboards, 26 unique uids
No overlaps, nothing outside the 24-column grid, one datasource throughout.

$ python3 Tests/assert_dashboard_queries.py Configuration/grafana/dashboards http://192.168.73.2:9090
26 dashboards, 1327 queries: 1314 returned data, 13 allowed empty, 0 unexpectedly empty, 0 errored
```

The allowed-empty list holds 39 titles before and after. Five of them were renamed, because the per-node guest CPU panel gained `· top 8`. How many actually come back empty tracks live state: 13 on this run.

A structural pass over the generated JSON confirms the intent landed: 0 text panels, all 271 stat tiles at `colorMode: value` and `graphMode: none`, all 372 time series on a list legend, 57 descriptions across 9 distinct texts, and 73 tinted single-series lines against 299 coloured by series name. That description count is the restyle as first built; the review below adds five more, which is why the table at the top of this record says 62 across 14.

## Deployment

The archive was split into four parts, uploaded over SFTP, reassembled and checked before anything was replaced. The reassembled archive hashed `b4abef1aa9148ecf02a0147dd16ab322fe9259c8fb0b15fb71bfd53568528f84`, matching the local build, and the extracted 26-file manifest hashed `73cd11146744ade398a25452a169ec97e31ae71e0fb5c70f66515519e56422ae`. The staged file list was diffed against the live one first and came back identical, so the copy replaced 26 files and orphaned none.

After the copy the live manifest hash under `/home/dkadi/monitoring/grafana/dashboards/` read `73cd11146744ade398a25452a169ec97e31ae71e0fb5c70f66515519e56422ae`, the same value, so what Grafana reads is byte-for-byte what the generator produced. The staging directory was removed.

Grafana was not restarted. It re-reads both provider directories every 30 seconds, and only a change to `provisioning/dashboards/homelab.yaml` needs a restart. The container's uptime still reads 3 days afterwards. No snapshot was taken and none was needed: the previous JSON is in git, and the generator rebuilds it.

Reading the specs back out of Grafana's own unified storage confirms it picked them up rather than merely that the files landed. All 26 dashboards are stored, and across them: 0 text panels, 271 stat tiles with 0 sparklines, 0 coloured backgrounds and all 271 centred, 372 time series with 0 legend tables, 73 tinted against 299 coloured by series name, and the 57 descriptions across 9 distinct texts that the restyle left. Every one of those matches the generated JSON, so Grafana's schema migration altered nothing on the way in. The review below then changed the description count and redeployed.

## Review and corrections

I reviewed the restyled set against live Prometheus before calling it done.
Making a denominator visible turns a quiet constant into a claim on screen, and two of the six constants
turned out to be wrong, with two more tiles pairing a correct denominator with a query that counted
something else. Both bad constants dated to the August rebuild and nobody had noticed, because a tile that
is permanently amber reads as a tile you have learned to ignore.

**Docker hosts reporting counted against nine.** There are eight cAdvisor hosts, in `inventory.py`, in the
scrape configuration and in the platform README. The tile read `8 / 9` and sat amber permanently. Now `8 / 8`.

**ZFS counted against seven.** `node_zfs_zpool_state` emits one series per pool state, and there are seven
states: online, degraded, faulted, offline, removed, suspended and unavail. There is one pool, `hddpool-1`.
The original panel read the seven state rows as seven datasets, so it demanded 7, got 1, and had been solid
red since it was written. The restyle then renamed it `ZFS datasets online`, which only made the title
agree with the wrong number. The review put the original title back, and `ZFS pools online` now reads
`1 / 1` in green.

**Both service tiles counted against nineteen while querying twenty.** `sum(probe_success)` includes the
alert bot's own health endpoint alongside the 19 published names, so the tile read `20 / 19`. Both are now
scoped to the published names and read `19 / 19`. The bot's probe is still covered by the health-check
table, which carries an unscoped `probe_success == 0` branch. Scrape targets down does not cover it: for a
blackbox target `up` says whether the exporter answered, not whether the probe succeeded, so a failing bot
health probe leaves `up` at 1 and never reaches that tile.

**The ingestion-rate graph drew two lines pretending to be one.**
`prometheus_tsdb_head_samples_appended_total` carries a `type` label, `float` and `histogram`, so the panel
drew two series in the same tint with the same legend. It is summed now, matching the tile above it.

**Every `out_of` unit rendered a double space.** Grafana maps `suffix:X` to `toFixedUnit(X, false)`, which
returns `{ text, suffix: " " + unit }` and supplies the separating space itself, so my leading space made
`5  / 5`. The helper no longer emits one.

**Three tiles sat amber with nothing left to explain them.** Interfaces down counts four parked devices,
Guests stopped counts templates and spares, and Guests with no backup counts every guest because this lab
keeps none. Each had carried a description that the restyle deleted with the rest of the prose. A tile that
is permanently coloured needs to say why, so those three got a short description back. That is the same test
the other eleven pass: it explains the number, it does not tell you what to think about it.

Two smaller things: `CPU throttling` was the only top-N panel whose title did not say so, and eleven names
were imported from `dashlib` and never used, two of them added by this change. Both are fixed.

The corrected set was deployed as a 22-operation patch against the live JSON rather than a wholesale
replacement, because only seven topic dashboards changed and no node board did. I reconstructed the deployed
state locally first and confirmed it matched the host byte for byte, generated the patch from the difference,
and proved against a copy that it reproduced the intended files exactly before sending it. After it ran, the
live manifest hashed `c114eebd51e373ce75a7724a5a0001ff559f74ee3658e537240882b342f779fd`, matching the
repository. An earlier draft of this record printed a hash captured between the last two files of that
patch, which matched neither side. Grafana was not restarted.

Re-verified after the corrections: 26 dashboards, 1,327 queries, 1,314 returning data, 13 allowed empty,
0 errored, no grid overlaps, and all six denominators now equal to what the live fleet reports.

## Second review

I ran the whole set past live Prometheus a second time, panel by panel, and this pass found defects the
restyle had inherited rather than caused. Nine of them made a panel state something untrue. None were
visible to `assert_dashboard_queries.py`, because every one of these queries returns data: it is the wrong
data, and "returned at least one series" cannot tell the difference.

**A mounted installation ISO pinned five panels at 100 percent.** [Issue 7](../Troubleshooting/Installation%20ISO%20Triggered%20Filesystem%20Capacity%20Alert%20-%202026-09-11.md)
excluded `udf` from the alert rule on 2026-09-11 and stopped there. The dashboards keep their own filesystem
selector in `inventory.py`, and it still admitted UDF, so Fullest filesystem read 100 percent in red,
Filesystems over 80% read 1, and the overview's *Anything failing a health check* table carried two rows for
`/dev/loop1`. That table is the overview's one "is anything wrong" panel and it had not been empty once since
the ISO was mounted. With `udf` excluded the fleet maximum is 77.9 percent, which is green.

**docker-main reported 77 percent CPU while running at 15.** An LXC is shown its node's whole CPU list but
only accumulates time on its own cpuset. docker-main lists 15 CPUs and four carry counters, so averaging
idle across all fifteen divided by the wrong number. `CPU by mode`, which normalises differently, read 4
percent on the same board at the same moment: two panels one row apart disagreeing by nineteen times.
`CORES` and `CPU_BUSY` now count only CPUs whose idle counter is advancing. docker-main reads 14.6 percent
and 4 cores; every other host's figure is unchanged to the decimal.

**Six LXC boards showed their hypervisor's uptime, and still show its disks.** `/proc/uptime` is not namespaced either. ansible-01 read
5d 19h against a real 2d 7h and docker-main 44d 11h against 10d 10h; the other four agreed only because they
had booted with their node. Uptime and Booted now come from `pve_uptime_seconds` for a container and stay on
node_exporter for a hypervisor. `/proc/diskstats` is not namespaced either and has no per-guest
substitute, so that section is titled *Node disk* on a container's board and carries one line saying the
devices and their traffic belong to the hypervisor.

**Every metal board listed all twenty fleet guests.** Only the first column of *Guests on <node>* carried the
node filter; the other five did not, and an outer join takes the union. green-server hosts no guests and its
table showed twenty rows belonging to other nodes, sorted so the fleet's busiest guest sat on top. All six
columns are scoped now: green-server 0, red-server 1, grey-server 12.

**Three tables joined on a key that repeats.** A table built from one query per column joins on a single
field, so that field has to be unique per row. *Containers* joined on the container name while eight hosts
run `cadvisor`, six run `wud` and four run `portainer_edge_agent`, and its memory, limit, age and network
columns were summed across the fleet: `cadvisor` reported 1.01 GB where the largest real instance is 202 MB.
*Filesystem headroom* joined 33 filesystems on 17 hosts, and *SMART* joined six disks on five hosts while its
temperature query returned seven rows, because red-server publishes SMART attribute 194 and 190 both. Each
now builds a composite key with `label_join` and lets only the first column carry the readable labels, so
every query returns exactly one row per key. cAdvisor also reports one series per interface in a container's
network namespace, so a `network_mode: host` container claimed every bridge on the box: four containers on
alpha-prod-01 each reported roughly twice the host NIC's entire traffic. The network columns now exclude the
bridges.

**The node_exporter Version column showed `1`.** It read the value of `node_exporter_build_info`, which is
always 1; the version is a label, and the column filter dropped it before the rename could reach it. The
label is kept now and the numeric column is hidden. The same collision sat in the per-host *Identity* table,
where three info metrics each carry a `version` label meaning the kernel build, the OS release and the
exporter version; the exporter's is relabelled before the join.

**The Updates column under-reported by up to 26 packages**, taking `max by (host)` of a metric published once
per origin. grey-server showed 51 against a real 77. It sums now.

**Two panels were coloured by thresholds that did not belong to them.** *Estimated draw* applied percentage
steps to a watt value, so the bar had been red at every load above 95 W and read red at 19 percent load; its
steps are scaled to the 900 W axis. *Errors and drops* sat orange permanently because the five hypervisor
NICs shed about 600 receive drops an hour as a steady state and the step was at 100; the step is above the
baseline now and the tile says what the baseline is. *Collectors erroring* counted node_exporter collectors
that returned nothing, which on this fleet is between two and twelve per host, so it was yellow on all
seventeen. Six of those collectors succeed on no host at all and are excluded; the column is *Collectors
inactive* and steps above the observed range.

**The alert bot appeared as a nameless row.** The blackbox name regex required a dot after the host part, so
`http://alert-bot:8080/health` came through with no `service` label and rendered blank in the reachability
timeline and the service table. The two 19/19 tiles had been scoped around it in the first review; the regex
is fixed now, so all twenty probes have names.

**Seven inventory flags were wrong**, and a wrong flag deletes a panel, which no test can see. grey-server
was marked as having neither NVMe nor SMART and has one NVMe device and three SMART disks, so the fleet's
busiest node had no drive-health panel on its own board. Five hosts run the apt textfile collector and were
marked as not having it, including grey-server with 77 packages pending and app-01 with 51. docker-main
reports 565 systemd units and had no *Failed units* panel. Four guests had the wrong parent node recorded:
alpha-prod-01, app-01 and edge-01 are on purple-server and ansible-01 is on blue-server, not grey-server as
the inventory said. Those corrections add six panels and nineteen queries.

**Denominators are derived rather than typed.** The first review corrected two wrong constants; this one
removes the class of error. `out_of()` now takes `len(inv.HYPERVISORS)` and the Docker host count from the
inventory, and the one denominator with no inventory source, the 19 published names, carries a comment
saying how to check it. The ZFS host was typed into five expressions and is derived too.

Smaller corrections: the per-host *Clock offset* tile compared a signed offset against absolute steps, so a
host drifting to minus half a second stayed green on its own board and orange on Monitoring; it takes `abs()`
now. The TSDB compaction graph used `$__interval`, which falls below the 15-second scrape interval as soon as
you zoom in and empties the panel; both targets use `$__rate_interval`. Two tables declared a Role column no
query could supply. Two dashboard descriptions still said nine cAdvisor hosts and 18 node_exporters. The
builder printed one node's panel count as if it were every node's, where the real range is 31 to 48. And
`build_dashboards.py` imported `dashlib` twice, once by wildcard and once by name; the wildcard is gone, which
is what let eleven unused imports accumulate unnoticed before.

Totals after this pass: 795 data panels, 1,346 queries, 69 panels carrying one of 15 texts, 45 titles
registered allowed-empty. The layout assertion passes and every query returns data or is registered as
correctly empty.

This build went up as a whole 26-file replacement over SSH rather than a patch, because the inventory
corrections change every node board. I read the live manifest first and it was `c114eebd`, the value the
first review left, so nothing had drifted underneath. The staged copy hashed the same as the repository
before anything was replaced, and the staged and live file lists were identical, so the copy replaced 26
files and orphaned none. Afterwards the live manifest reads
`a69a910a3d9e9f9c6ef0e12ae16e9d2f6be216ea64df9b3713fe5e958dffded5`, matching the repository.

Grafana was not restarted and its uptime still dates to 2026-09-11 with a restart count of zero. Reading
the current specs back out of unified storage confirms it re-read the files on its own interval: 26
dashboards stored under 26 unique uids, one of them carrying the new panel title `Collectors inactive`
and none still carrying the old `Collectors erroring`.

The same review read the 24 alert rules and found one that could never fire. That is a separate matter with
its own record and its own deployment, which did need a Grafana restart:
[issue 8](../Troubleshooting/Exporter%20Down%20Alert%20Could%20Never%20Fire%20-%202026-09-14.md).

## What did not change

Panel types, dashboard UIDs, folder layout, the two header dropdowns, the alert rules and the scrape configuration are all untouched. 96 base threshold steps changed colour only, from `text` to the neutral tint, and the only operational cutoffs that moved are the two the review corrects: Docker hosts reporting from `orange 8 / green 9` to `orange 7 / green 8`, and ZFS pools online from `green 7` to `green 1`. Queries are unchanged apart from the three the review section corrects. The 24 alert rules and their routing were not part of this and were not read. Temperatures still display in Fahrenheit with the conversion in the query.
