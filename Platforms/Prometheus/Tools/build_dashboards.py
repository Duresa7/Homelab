#!/usr/bin/env python3
"""Generate every Homelab Grafana dashboard from one description.

Run it, commit what it writes, deploy the directory. Nothing else edits the
dashboard JSON.

    python3 Tools/build_dashboards.py

Output:
    Configuration/grafana/dashboards/homelab/*.json   -> Grafana folder "Homelab"
    Configuration/grafana/dashboards/nodes/*.json     -> Grafana folder "Nodes"
    Tests/allow-empty.json                            -> read by the query assertion

Why generated. There is one dashboard per host, and eighteen hand-maintained
copies of the same layout diverge the first time one of them is edited. The
per-node layout lives in `node_dashboard()` once, and each host's capability
flags in `inventory.py` decide which sections it grows.

Panel form follows the data's job rather than habit:

    a single current value            stat tile, with a sparkline if the trend helps
    a ratio against a known limit     bar gauge, one bar per thing
    change over time, <= 8 series     time series
    change over time, many series     time series of the top N, plus a table that
                                      covers all of them
    up or down over time              state timeline
    one row per thing, many columns   table, with the magnitude column drawn as
                                      an in-cell bar
    a list that should normally be
    empty                             table, with the empty state spelled out

Two rules the colours follow. Green, amber and red are reserved for state, so no
series ever wears them for identity. Multi-series graphs colour by series name,
so a host keeps its colour when a filter changes how many series are drawn.
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from dashlib import *          # noqa: F403
from dashlib import (BY_NAME, CELL_COLOR_BG, CELL_COLOR_TEXT, CERT_DAYS, DS,
                     GOOD_ABOVE_ZERO, BAD_ABOVE_ZERO, Grid, LEGEND_LIST,
                     LEGEND_OFF, LEGEND_TABLE, LOAD_PER_CORE, MAP_OK_FAIL,
                     MAP_UP_DOWN, PCT_LOAD, PCT_USED, TEMP_F, TEXT_ONLY,
                     TOOLTIP_MULTI, TOOLTIP_SINGLE, bargauge, by_name, by_regex,
                     cell_gauge, dash_links, dashboard, fixed, gauge, heatmap,
                     mapping, override, q, stat, state_timeline, table, text,
                     thresholds, timeseries, tq, var_constant, var_custom,
                     var_query)
import inventory as inv
from inventory import CT, DISK, FS, NET, PKG_TEMP_F, sel

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_TOPIC = ROOT / "Configuration/grafana/dashboards/homelab"
OUT_NODES = ROOT / "Configuration/grafana/dashboards/nodes"

# Panels that are correct when they draw nothing. A restart table with no rows
# means nothing restarted. Registering the title here is what stops
# assert_dashboard_queries.py treating the healthy state as a failure.
ALLOW_EMPTY: set[str] = set()


def empty_ok(panel: dict) -> dict:
    ALLOW_EMPTY.add(panel["title"])
    return panel


def joined_table(title, columns, *, w=24, h=11, desc="", sort=None, extra_overrides=None,
                 join_on="host", keep=r"^(host|role|Value #.*)$", no_value="no data"):
    """A table built from one query per column, joined on a shared label.

    `columns` is a list of (refId, expr, display name, [field overrides]).
    Each query must aggregate down to the join label so the join has nothing
    ambiguous to match on.
    """
    targets, rename, order, overrides = [], {}, {}, []
    for i, (ref, expr, name, props) in enumerate(columns):
        targets.append(tq(expr, ref=ref))
        rename["Value #" + ref] = name
        order[name] = i + 2
        if props:
            overrides.append(by_name(name, props))
    order.setdefault("host", 0)
    order.setdefault("role", 1)
    return table(
        title, targets, w=w, h=h, desc=desc, sort=sort, no_value=no_value,
        transformations=[
            {"id": "joinByField", "options": {"byField": join_on, "mode": "outer"}},
            {"id": "filterFieldsByName", "options": {"include": {"pattern": keep}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName": rename,
                                           "indexByName": order}},
        ],
        overrides=overrides + (extra_overrides or []),
    )


HOST_LINK = ("links", [{"title": "Open this node's dashboard",
                        "url": "/d/node-${__value.raw}", "targetBlank": False}])

NAV = """
| | | |
|---|---|---|
| **[Overview](/d/homelab-overview)** — is anything wrong | **[Nodes](/dashboards/f/nodes)** — one dashboard per host | **[Proxmox](/d/proxmox-cluster)** — cluster, guests, storage |
| **[Services](/d/services-uptime)** — reachability and TLS | **[Containers](/d/containers)** — every Docker workload | **[Storage](/d/storage-health)** — capacity and drive health |
| **[Network](/d/network)** — throughput, errors, TCP | **[Power](/d/power-ups)** — both UPS units | **[Monitoring](/d/monitoring-health)** — does Prometheus itself work |
| **[TeamSpeak](/d/teamspeak)** — voice reachability | | |
"""


# ============================================================ Homelab Overview

def overview():
    g = Grid()

    g.section("Right now", "Eight numbers that answer *is anything wrong*. "
                           "Everything below, and every dashboard in the header dropdowns, is detail behind them.")
    g.extend([
        stat("Cluster quorum", [q('pve_up{id="cluster/Galaxy"}', instant=True)], w=6,
             mappings=mapping({0: ("NOT QUORATE", "red"), 1: ("QUORATE", "green")}),
             thr=GOOD_ABOVE_ZERO, color_mode="background", text_mode="value",
             desc="Corosync quorum on Galaxy. Without it Proxmox refuses to start or migrate a guest."),
        stat("Proxmox nodes online", [q('sum(pve_up{id=~"node/.*"})', instant=True)], w=6,
             thr=thresholds(("red", None), ("orange", 4), ("green", 5)), maxv=5,
             desc="Out of five."),
        stat("Guests running", [q('sum(pve_up{id=~"(qemu|lxc)/.*"})', instant=True)], w=6,
             thr=TEXT_ONLY, color_mode="none", graph="area",
             desc="Every VM and container Proxmox reports as running."),
        stat("Services reachable", [q("sum(probe_success)", instant=True)], w=6,
             thr=thresholds(("red", None), ("orange", 18), ("green", 19)), maxv=19,
             desc="Out of nineteen internal service names, probed end to end through Nginx Proxy Manager."),
        stat("Scrape targets down", [q("count(up == 0) or vector(0)", instant=True)], w=6,
             thr=BAD_ABOVE_ZERO, color_mode="background",
             desc="A target down means a blind spot, not necessarily an outage."),
        stat("UPS on mains", [q('min(nut_ups_status{status="OL"})', instant=True)], w=6,
             mappings=mapping({0: ("ON BATTERY", "red"), 1: ("ON MAINS", "green")}),
             thr=GOOD_ABOVE_ZERO, color_mode="background", text_mode="value",
             desc="Red as soon as either UPS drops off mains."),
        stat("Hottest CPU package", [q("max(%s)" % (PKG_TEMP_F % 'role="hypervisor"'), instant=True)],
             w=6, unit="fahrenheit", decimals=0, thr=TEMP_F, graph="area",
             desc="The warmest of the five nodes, at the die rather than a core."),
        stat("Fullest filesystem", [q("max(%s)" % inv.fs_used_pct(), instant=True)], w=6,
             unit="percent", decimals=1, thr=PCT_USED, graph="area",
             desc="The single tightest mount anywhere in the fleet."),
    ])

    g.section("Needs attention",
              "One table, ten health checks, and a row only when something fails one of them. "
              "Empty is the goal.")
    g.add(empty_ok(table(
        "Anything failing a health check",
        [tq(NEEDS_ATTENTION)],
        h=8,
        no_value="All clear — nothing is failing a health check.",
        desc="Scrape targets down, services unreachable, certificates inside 21 days, ZFS pools not "
             "online, NVMe critical warnings or spare under 10%, filesystems over 90% or mounted "
             "read-only, a UPS on battery, a SMART self-assessment that failed, and either TeamSpeak "
             "fault. The value column carries whichever number the check is about.",
        transformations=[
            {"id": "filterFieldsByName",
             "options": {"include": {"pattern": r"^(check|object|host|Value)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                {"check": "Check", "object": "Object", "host": "Host", "Value": "Reading"},
             "indexByName": {"check": 0, "object": 1, "host": 2, "Value": 3}}},
        ],
        overrides=[by_name("Check", [CELL_COLOR_BG, ("thresholds", thresholds(("red", None)))])],
        sort=("Check", False))))

    g.section("Nodes", "Every host that carries a workload. Click a hostname to open that node's own dashboard.")
    g.add(joined_table(
        "Fleet",
        [("A", 'max by (host, role) (up{job="node"})', "Up",
          [CELL_COLOR_BG, ("mappings", MAP_UP_DOWN), ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 70)]),
         ("B", "max by (host) (time() - node_boot_time_seconds)", "Uptime",
          [("unit", "s"), ("decimals", 0), ("custom.width", 120)]),
         ("C", "count by (host) (count by (host, cpu) (node_cpu_seconds_total))", "Cores",
          [("custom.width", 70)]),
         ("D", inv.CPU_BUSY % "", "CPU",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_LOAD)] + cell_gauge()),
         ("E", "max by (host) (node_load1) / on (host) group_left () "
               "count by (host) (count by (host, cpu) (node_cpu_seconds_total))", "Load / core",
          [("decimals", 2), ("thresholds", LOAD_PER_CORE), CELL_COLOR_TEXT, ("custom.width", 100)]),
         ("F", inv.MEM_USED % ("", ""), "Memory",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge()),
         ("G", "max by (host) (node_memory_MemTotal_bytes)", "RAM",
          [("unit", "bytes"), ("decimals", 0), ("custom.width", 90)]),
         ("H", 'max by (host) (%s)' % inv.fs_used_pct('mountpoint="/"'), "Root FS",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge()),
         ("I", "max by (host) (%s)" % (PKG_TEMP_F % 'role="hypervisor"'), "CPU temp",
          [("unit", "fahrenheit"), ("decimals", 0), ("thresholds", TEMP_F), CELL_COLOR_TEXT,
           ("custom.width", 100), ("noValue", "—")])],
        h=12, sort=("CPU", True),
        desc="Sorted by CPU. The temperature column is blank for guests on purpose: an LXC reads the "
             "node's sensors, not its own, so the number would belong to a different machine.",
        extra_overrides=[by_name("host", [HOST_LINK, ("custom.width", 150),
                                          ("displayName", "Host")]),
                         by_name("role", [("custom.width", 110), ("displayName", "Role")])]))
    g.extend([
        timeseries("CPU busy — five busiest hosts",
                   [q("topk(5, %s)" % (inv.CPU_BUSY % ""), "{{host}}")],
                   unit="percent", maxv=100, h=8, thr=PCT_LOAD,
                   desc="Top five only, so the graph stays readable. The Fleet table above covers all eighteen."),
        timeseries("Memory used — five fullest hosts",
                   [q("topk(5, %s)" % (inv.MEM_USED % ("", "")), "{{host}}")],
                   unit="percent", maxv=100, h=8, thr=PCT_USED,
                   desc="Top five only. The Fleet table above covers all eighteen."),
    ])

    g.section("Services", "Every internal name, probed through the proxy a person actually goes through.")
    g.add(state_timeline(
        "Reachability", [q("probe_success", "{{instance}}")], h=10,
        mappings=mapping({0: ("down", "red"), 1: ("up", "green")}),
        legend=LEGEND_OFF,
        desc="One band per service. A gap is a scrape that never happened; red is a probe that ran and failed.",
        overrides=[]))

    g.section("Where to look next", "")
    g.add(text(NAV, h=7))

    return dashboard(
        "homelab-overview", "Homelab Overview", g,
        tags=["homelab", "overview"],
        description="The landing page. Fleet health first, then the node table, then everything else "
                    "behind the dropdowns in the header.",
        refresh="30s", time_from="now-6h")


# The ten checks, unioned into one vector. Each arm labels itself with `check`
# and `object` so the table has stable columns whatever fires, and each arm is a
# filtered comparison, so a healthy fleet returns nothing at all.
#
# SMART is gated on smart_available. Both QEMU guests expose a virtual
# /dev/sda whose self-assessment is absent rather than failed, and reporting
# "SMART not healthy" for a disk that has no SMART is a false alarm that trains
# you to ignore the panel. NVMe health is not lost by that gate: it arrives
# through nvme_critical_warning and the spare check instead.
NEEDS_ATTENTION = " or ".join([
    'label_replace(label_replace(up == 0, "check", "scrape target down", "", ""),'
    ' "object", "$1", "instance", "(.*)")',

    'label_replace(label_replace(probe_success == 0, "check", "service unreachable", "", ""),'
    ' "object", "$1", "instance", "(.*)")',

    'label_replace(label_replace(round((probe_ssl_earliest_cert_expiry - time()) / 86400) < 21,'
    ' "check", "TLS certificate expiring (days)", "", ""), "object", "$1", "instance", "(.*)")',

    'label_replace(label_replace(max by (host, zpool) (node_zfs_zpool_state{state!="online"}) == 1,'
    ' "check", "ZFS pool not online", "", ""), "object", "$1", "zpool", "(.*)")',

    'label_replace(label_replace(nvme_critical_warning > 0,'
    ' "check", "NVMe critical warning", "", ""), "object", "$1", "device", "(.*)")',

    'label_replace(label_replace(round(100 * nvme_available_spare_ratio) < 10,'
    ' "check", "NVMe spare remaining (%)", "", ""), "object", "$1", "device", "(.*)")',

    'label_replace(label_replace(round(%s) > 90,'
    ' "check", "filesystem over 90%% (used %%)", "", ""), "object", "$1", "mountpoint", "(.*)")'
    % inv.fs_used_pct(),

    'label_replace(label_replace(node_filesystem_readonly{%s} == 1,'
    ' "check", "filesystem read-only", "", ""), "object", "$1", "mountpoint", "(.*)")' % FS,

    'label_replace(label_replace(nut_ups_status{status="OB"} == 1,'
    ' "check", "UPS on battery", "", ""), "object", "$1", "ups", "(.*)")',

    'label_replace(label_replace(smartmon_device_smart_healthy == 0'
    ' and on (host, disk) smartmon_device_smart_available == 1,'
    ' "check", "SMART self-assessment failed", "", ""), "object", "$1", "disk", "(.*)")',

    'label_replace(label_replace(teamspeak_server_fault == 1,'
    ' "check", "TeamSpeak voice down", "", ""), "object", "$1", "server", "(.*)")',

    'label_replace(label_replace(teamspeak_tunnel_fault == 1,'
    ' "check", "TeamSpeak public path down", "", ""), "object", "$1", "server", "(.*)")',
])


# =========================================================== Proxmox / Galaxy

GUEST = 'id=~"(qemu|lxc)/.*"'
NODE_ID = 'id=~"node/.*"'


def proxmox():
    g = Grid()

    g.section("Cluster", "Galaxy as one machine: does it have quorum, and is everything that should be "
                         "running actually running.")
    g.extend([
        stat("Quorum", [q('pve_up{id="cluster/Galaxy"}', instant=True)], w=4,
             mappings=mapping({0: ("NOT QUORATE", "red"), 1: ("QUORATE", "green")}),
             thr=GOOD_ABOVE_ZERO, color_mode="background", text_mode="value"),
        stat("Nodes online", [q("sum(pve_up{%s})" % NODE_ID, instant=True)], w=4,
             thr=thresholds(("red", None), ("orange", 4), ("green", 5)), maxv=5),
        stat("Guests running", [q("sum(pve_up{%s})" % GUEST, instant=True)], w=4,
             color_mode="none", graph="area"),
        stat("Guests stopped", [q("count(pve_up{%s} == 0) or vector(0)" % GUEST, instant=True)], w=4,
             thr=thresholds(("green", None), ("yellow", 1)),
             desc="Stopped is not always wrong — templates and spare guests live here too."),
        stat("Templates", [q('sum(pve_guest_info{template="1"})', instant=True)], w=4,
             color_mode="none"),
        stat("Guests with no backup", [q("sum(pve_not_backed_up_total) or vector(0)", instant=True)], w=4,
             thr=thresholds(("green", None), ("orange", 1)),
             desc="Proxmox reports a guest as not backed up when no vzdump archive exists for it on any "
                  "storage it can see. It says nothing about backups taken outside Proxmox."),
    ])

    g.section("Nodes", "The five machines under the cluster. Click a node to open its own dashboard.")
    g.add(joined_table(
        "Node summary",
        [("A", "pve_up{%s}" % NODE_ID, "Up",
          [CELL_COLOR_BG, ("mappings", MAP_UP_DOWN), ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 70)]),
         ("B", "pve_uptime_seconds{%s}" % NODE_ID, "Uptime", [("unit", "s"), ("decimals", 0)]),
         ("C", "pve_cpu_usage_ratio{%s} * 100" % NODE_ID, "CPU",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_LOAD)] + cell_gauge()),
         ("D", "pve_cpu_usage_limit{%s}" % NODE_ID, "Cores", [("custom.width", 70)]),
         ("E", "pve_memory_usage_bytes{%s} / pve_memory_size_bytes{%s} * 100" % (NODE_ID, NODE_ID), "Memory",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge()),
         ("F", "pve_memory_size_bytes{%s}" % NODE_ID, "RAM", [("unit", "bytes"), ("decimals", 0)]),
         ("G", 'label_replace(count by (node) ((pve_up{%s} == 1)'
               ' * on (id) group_left (node) pve_guest_info), "id", "node/$1", "node", "(.*)")' % GUEST,
          "Guests running", [("custom.width", 130), ("noValue", "0"), ("decimals", 0)])],
        h=8, join_on="id", keep=r"^(id|Value #.*)$", sort=("CPU", True),
        desc="Proxmox's own view of each node, from the PVE API rather than from node_exporter. The two "
             "disagree slightly by design: this one counts a node's memory the way the hypervisor does.",
        extra_overrides=[by_name("id", [
            ("displayName", "Node"), ("custom.width", 170),
            ("links", [{"title": "Open this node's dashboard",
                        "url": "/d/node-${__data.fields.id:raw}", "targetBlank": False}])])]))
    g.extend([
        timeseries("Node CPU", [q("pve_cpu_usage_ratio{%s} * 100" % NODE_ID, "{{id}}")],
                   unit="percent", maxv=100, h=8, thr=PCT_LOAD),
        timeseries("Node memory used",
                   [q("pve_memory_usage_bytes{%s} / pve_memory_size_bytes{%s} * 100" % (NODE_ID, NODE_ID),
                      "{{id}}")],
                   unit="percent", maxv=100, h=8, thr=PCT_USED),
    ])

    g.section("Guests", "Every VM and container the cluster knows about, including templates.")
    g.add(joined_table(
        "Every guest",
        [("A", "pve_up{%s} * on (id) group_left (name, node, type) pve_guest_info" % GUEST, "Up",
          [CELL_COLOR_BG, ("mappings", MAP_UP_DOWN), ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 70)]),
         ("B", "pve_cpu_usage_ratio{%s} * 100" % GUEST, "CPU",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_LOAD)] + cell_gauge()),
         ("C", "pve_cpu_usage_limit{%s}" % GUEST, "Cores", [("custom.width", 70)]),
         ("D", "pve_memory_usage_bytes{%s} / pve_memory_size_bytes{%s} * 100" % (GUEST, GUEST), "Memory",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge()),
         ("E", "pve_memory_size_bytes{%s}" % GUEST, "RAM", [("unit", "bytes"), ("decimals", 0)]),
         ("F", "pve_disk_size_bytes{%s}" % GUEST, "Disk", [("unit", "bytes"), ("decimals", 0)]),
         ("G", "pve_uptime_seconds{%s}" % GUEST, "Uptime", [("unit", "s"), ("decimals", 0)]),
         ("H", "pve_not_backed_up_info", "Backed up",
          [("mappings", mapping({0: ("yes", "green"), 1: ("no", "orange")}, default=("yes", "green"))),
           CELL_COLOR_TEXT, ("custom.width", 100)])],
        h=14, join_on="id", keep=r"^(id|name|node|type|Value #.*)$", sort=("CPU", True),
        desc="Sorted by CPU. A guest name links to that host's own dashboard where one exists; the two "
             "templates and kali-pen have no node_exporter, so those links go nowhere.",
        extra_overrides=[
            by_name("id", [("displayName", "ID"), ("custom.width", 90)]),
            by_name("name", [("displayName", "Guest"), ("custom.width", 170),
                             ("links", [{"title": "Open this host's dashboard",
                                         "url": "/d/node-${__value.raw}", "targetBlank": False}])]),
            by_name("node", [("displayName", "On node"), ("custom.width", 140),
                             ("links", [{"title": "Open this node's dashboard",
                                         "url": "/d/node-${__value.raw}", "targetBlank": False}])]),
            by_name("type", [("displayName", "Type"), ("custom.width", 80)])]))
    g.extend([
        timeseries("Guest CPU — eight busiest",
                   [q("topk(8, pve_cpu_usage_ratio{%s} * 100)" % GUEST, "{{id}}")],
                   unit="percent", h=8, thr=PCT_LOAD,
                   desc="Top eight. The guest table above covers every one."),
        timeseries("Guest memory — eight fullest",
                   [q("topk(8, pve_memory_usage_bytes{%s} / pve_memory_size_bytes{%s} * 100)" % (GUEST, GUEST),
                      "{{id}}")],
                   unit="percent", maxv=100, h=8, thr=PCT_USED,
                   desc="Top eight. The guest table above covers every one."),
    ])

    g.section("Guest I/O", "Which guests are actually moving bytes.")
    g.extend([
        timeseries("Guest disk read — eight busiest",
                   [q("topk(8, rate(pve_disk_read_bytes_total{%s}[$__rate_interval]))" % GUEST, "{{id}}")],
                   unit="Bps", h=8),
        timeseries("Guest disk write — eight busiest",
                   [q("topk(8, rate(pve_disk_written_bytes_total{%s}[$__rate_interval]))" % GUEST, "{{id}}")],
                   unit="Bps", h=8),
        timeseries("Guest network in — eight busiest",
                   [q("topk(8, rate(pve_network_receive_bytes_total{%s}[$__rate_interval]))" % GUEST, "{{id}}")],
                   unit="Bps", h=8),
        timeseries("Guest network out — eight busiest",
                   [q("topk(8, rate(pve_network_transmit_bytes_total{%s}[$__rate_interval]))" % GUEST, "{{id}}")],
                   unit="Bps", h=8),
    ])

    g.section("Storage", "Every storage the cluster can see, on every node that can see it.")
    g.add(bargauge(
        "Storage used",
        [q("pve_disk_usage_bytes{id=~\"storage/.*\"} / pve_disk_size_bytes{id=~\"storage/.*\"} * 100",
           "{{id}}", instant=True)],
        w=12, h=11, desc="A shared storage appears once per node that mounts it."))
    g.add(joined_table(
        "Storage headroom",
        [("A", 'pve_disk_usage_bytes{id=~"storage/.*"} / pve_disk_size_bytes{id=~"storage/.*"} * 100', "Used",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge()),
         ("B", 'pve_disk_size_bytes{id=~"storage/.*"} - pve_disk_usage_bytes{id=~"storage/.*"}', "Free",
          [("unit", "bytes"), ("decimals", 0)]),
         ("C", 'pve_disk_size_bytes{id=~"storage/.*"}', "Size", [("unit", "bytes"), ("decimals", 0)]),
         ("D", 'pve_storage_shared', "Shared",
          [("mappings", mapping({0: ("no", "text"), 1: ("yes", "text")})), ("custom.width", 90)])],
        w=12, h=11, join_on="id", keep=r"^(id|Value #.*)$", sort=("Used", True),
        extra_overrides=[by_name("id", [("displayName", "Storage"), ("custom.width", 240)])]))

    return dashboard(
        "proxmox-cluster", "Proxmox · Galaxy Cluster", g,
        tags=["homelab", "proxmox"],
        description="The cluster as Proxmox itself sees it: quorum, the five nodes, every guest, and the "
                    "storages behind them.",
        refresh="30s", time_from="now-6h")


# ================================================================= Containers

def containers():
    g = Grid()
    hosts = 'host=~"$dockerhost"'
    ct = sel(CT, hosts, 'name=~"$container"')

    g.section("Fleet", "Fifty-odd containers across nine Docker hosts, as one population.")
    g.extend([
        stat("Containers running", [q("count(container_last_seen{%s})" % ct, instant=True)], w=4,
             color_mode="none", graph="area"),
        stat("Docker hosts reporting", [q("count(count by (host) (container_last_seen{%s}))" % CT, instant=True)],
             w=4, thr=thresholds(("red", None), ("orange", 8), ("green", 9)), maxv=9,
             desc="Out of nine. A host missing here means cAdvisor is down, not that its containers are."),
        stat("Started in the last hour",
             [q("count(time() - container_start_time_seconds{%s} < 3600) or vector(0)" % ct, instant=True)],
             w=4, thr=thresholds(("green", None), ("yellow", 1), ("orange", 3)),
             desc="A deliberate deploy and a crash loop look identical here; the table below tells them apart."),
        stat("OOM kills, last 24h",
             [q("sum(increase(container_oom_events_total{%s}[24h])) or vector(0)" % ct, instant=True)],
             w=4, thr=BAD_ABOVE_ZERO, color_mode="background"),
        stat("Being CPU throttled",
             [q("count(rate(container_cpu_cfs_throttled_seconds_total{%s}[$__rate_interval]) > 0) or vector(0)" % ct,
                instant=True)],
             w=4, thr=thresholds(("green", None), ("yellow", 1)),
             desc="Throttling means the container is hitting its CPU quota, not that the host is busy."),
        stat("Memory in containers",
             [q("sum(container_memory_working_set_bytes{%s})" % ct, instant=True)],
             w=4, unit="bytes", decimals=1, color_mode="none", graph="area"),
    ])

    g.section("Restarts and faults", "These three tables are empty when nothing is wrong.")
    g.add(empty_ok(table(
        "Started in the last 6 hours",
        [tq("time() - container_start_time_seconds{%s} < 21600" % ct)],
        w=12, h=8, unit="s", no_value="Nothing has restarted in the last 6 hours.",
        desc="Age since start, youngest first. A container that keeps reappearing at the top is looping.",
        transformations=[
            {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(host|name|image|Value)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                {"host": "Host", "name": "Container", "image": "Image", "Value": "Running for"},
             "indexByName": {"name": 0, "host": 1, "image": 2, "Value": 3}}}],
        sort=("Running for", False),
        overrides=[by_name("Running for", [("unit", "s"), ("decimals", 0), CELL_COLOR_TEXT,
                                           ("thresholds", thresholds(("red", None), ("orange", 900), ("green", 3600)))])])))
    g.add(empty_ok(table(
        "OOM kills, last 24 hours",
        [tq("increase(container_oom_events_total{%s}[24h]) > 0" % ct)],
        w=12, h=8, no_value="No container has been OOM killed in 24 hours.",
        desc="The kernel killed the process for exceeding memory. Raise the limit or fix the leak.",
        transformations=[
            {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(host|name|Value)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                {"host": "Host", "name": "Container", "Value": "Kills"}, "indexByName": {"name": 0, "host": 1, "Value": 2}}}],
        sort=("Kills", True),
        overrides=[by_name("Kills", [CELL_COLOR_BG, ("thresholds", BAD_ABOVE_ZERO), ("decimals", 0)])])))

    g.section("CPU", "Container CPU is a share of the whole host, so 100% means one full core.")
    g.extend([
        timeseries("CPU — ten busiest containers",
                   [q("topk(10, sum by (host, name) (rate(container_cpu_usage_seconds_total{%s}[$__rate_interval])) * 100)" % ct,
                      "{{name}} · {{host}}")],
                   unit="percent", h=9,
                   desc="Top ten. The table below covers every container."),
        timeseries("CPU throttling",
                   [q("topk(10, sum by (host, name) (rate(container_cpu_cfs_throttled_seconds_total{%s}[$__rate_interval])) * 100)" % ct,
                      "{{name}} · {{host}}")],
                   unit="percent", h=9, thr=thresholds(("green", None), ("orange", 1)),
                   desc="Seconds of runnable-but-not-scheduled time per second. Flat zero is the healthy shape."),
    ])

    g.section("Memory", "Working set, which is what the kernel would have to reclaim.")
    g.extend([
        timeseries("Memory — ten largest containers",
                   [q("topk(10, sum by (host, name) (container_memory_working_set_bytes{%s}))" % ct,
                      "{{name}} · {{host}}")],
                   unit="bytes", h=9, desc="Top ten. The table below covers every container."),
        timeseries("Memory by host",
                   [q("sum by (host) (container_memory_working_set_bytes{%s})" % ct, "{{host}}")],
                   unit="bytes", h=9, stack=True,
                   desc="Stacked, so the height is the fleet's total container memory."),
    ])

    g.section("Every container", "One row per container. Filter with the header dropdowns or the column filters.")
    g.add(joined_table(
        "Containers",
        [("A", "sum by (host, name, image) (rate(container_cpu_usage_seconds_total{%s}[$__rate_interval])) * 100" % ct,
          "CPU", [("unit", "percent"), ("decimals", 2), ("thresholds", PCT_LOAD)] + cell_gauge(0, 200)),
         ("B", "sum by (name) (container_memory_working_set_bytes{%s})" % ct, "Memory",
          [("unit", "bytes"), ("decimals", 1)]),
         ("C", "sum by (name) (container_spec_memory_limit_bytes{%s} > 0)" % ct, "Limit",
          [("unit", "bytes"), ("decimals", 1), ("noValue", "none")]),
         ("D", "max by (name) (time() - container_start_time_seconds{%s})" % ct, "Up for",
          [("unit", "s"), ("decimals", 0)]),
         ("E", "sum by (name) (rate(container_network_receive_bytes_total{%s}[$__rate_interval]))" % ct, "Net in",
          [("unit", "Bps"), ("decimals", 1)]),
         ("F", "sum by (name) (rate(container_network_transmit_bytes_total{%s}[$__rate_interval]))" % ct, "Net out",
          [("unit", "Bps"), ("decimals", 1)])],
        h=16, join_on="name", keep=r"^(name|host|image|Value #.*)$", sort=("CPU", True),
        desc="Only two containers set a memory limit, so most rows show none. Without a limit the host's "
             "memory is the limit.",
        extra_overrides=[
            by_name("name", [("displayName", "Container"), ("custom.width", 220)]),
            by_name("host", [("displayName", "Host"), ("custom.width", 140), HOST_LINK]),
            by_name("image", [("displayName", "Image")])]))

    g.section("Network and disk", "Container traffic, separate from the host's own.")
    g.extend([
        timeseries("Network in — ten busiest",
                   [q("topk(10, sum by (host, name) (rate(container_network_receive_bytes_total{%s}[$__rate_interval])))" % ct,
                      "{{name}} · {{host}}")], unit="Bps", h=9),
        timeseries("Network out — ten busiest",
                   [q("topk(10, sum by (host, name) (rate(container_network_transmit_bytes_total{%s}[$__rate_interval])))" % ct,
                      "{{name}} · {{host}}")], unit="Bps", h=9),
        timeseries("Writable layer size",
                   [q("topk(10, sum by (host, name) (container_fs_usage_bytes{%s}))" % ct, "{{name}} · {{host}}")],
                   unit="bytes", h=9, w=24,
                   desc="Bytes written into the container's own layer rather than into a volume. Steady growth "
                        "here is usually a log file nobody rotates."),
    ])

    return dashboard(
        "containers", "Containers", g,
        tags=["homelab", "containers"],
        description="Every Docker workload across the nine cAdvisor hosts.",
        refresh="1m", time_from="now-6h",
        templating=[
            var_query("dockerhost", "Host", 'label_values(container_last_seen{name!=""}, host)'),
            var_query("container", "Container", 'label_values(container_last_seen{name!=""}, name)'),
        ])


# =========================================================== Services, uptime

# The blackbox job carries the full URL in `instance` and nothing else, so every
# panel that wants a readable name strips the scheme and the domain here rather
# than showing nineteen copies of ".alphasecunited.com".
SVC_NAME = ('label_replace(%s, "service", "$1", "instance",'
            ' "https?://([^.]+)\\\\..*")')


def services():
    g = Grid()
    svc = 'instance=~"$service"'

    g.section("Right now", "Each probe goes through Nginx Proxy Manager, so a failure means the path a "
                           "person actually uses is broken: local DNS, the proxy, the certificate, or the "
                           "backend behind it.")
    g.extend([
        stat("Reachable", [q("sum(probe_success)", instant=True)], w=4,
             thr=thresholds(("red", None), ("orange", 18), ("green", 19)), maxv=19,
             desc="Out of nineteen."),
        stat("Failing", [q("count(probe_success == 0) or vector(0)", instant=True)], w=4,
             thr=BAD_ABOVE_ZERO, color_mode="background"),
        stat("Slowest probe", [q("max(probe_duration_seconds)", instant=True)], w=4,
             unit="s", decimals=2, thr=thresholds(("green", None), ("yellow", 1), ("orange", 3), ("red", 8)),
             graph="area"),
        stat("Median probe", [q("quantile(0.5, probe_duration_seconds)", instant=True)], w=4,
             unit="s", decimals=3, color_mode="none", graph="area"),
        stat("Nearest certificate expiry",
             [q("min((probe_ssl_earliest_cert_expiry - time()) / 86400)", instant=True)], w=4,
             unit="d", decimals=0, thr=CERT_DAYS,
             desc="Days left on the soonest-expiring certificate in the chain NPM serves."),
        stat("24-hour availability", [q("avg(avg_over_time(probe_success[24h])) * 100", instant=True)], w=4,
             unit="percent", decimals=3,
             thr=thresholds(("red", None), ("orange", 99), ("yellow", 99.5), ("green", 99.9)),
             desc="Averaged across all nineteen probes over the last 24 hours, regardless of the time picker."),
    ])

    g.section("Availability", "One band per service. A gap is a scrape that never ran; red is a probe that "
                              "ran and failed.")
    g.add(state_timeline(
        "Reachability", [q(SVC_NAME % "probe_success", "{{service}}")], h=11,
        mappings=mapping({0: ("down", "red"), 1: ("up", "green")}), legend=LEGEND_OFF))
    g.add(joined_table(
        "Every service",
        [("A", SVC_NAME % "probe_success", "Up",
          [CELL_COLOR_BG, ("mappings", MAP_UP_DOWN), ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 70)]),
         ("B", SVC_NAME % "avg_over_time(probe_success[24h]) * 100", "24h uptime",
          [("unit", "percent"), ("decimals", 3), ("thresholds", thresholds(("red", None), ("orange", 99), ("green", 99.9)))]
          + cell_gauge()),
         ("C", SVC_NAME % "probe_duration_seconds", "Total",
          [("unit", "s"), ("decimals", 3),
           ("thresholds", thresholds(("green", None), ("yellow", 1), ("orange", 3)))] + cell_gauge(0, 5)),
         ("D", SVC_NAME % "probe_http_status_code", "HTTP",
          [CELL_COLOR_TEXT, ("custom.width", 80), ("decimals", 0),
           ("thresholds", thresholds(("green", None), ("yellow", 400), ("red", 500)))]),
         ("E", SVC_NAME % "probe_http_version", "Ver", [("decimals", 1), ("custom.width", 70)]),
         ("F", SVC_NAME % "probe_http_redirects", "Hops", [("decimals", 0), ("custom.width", 70)]),
         ("G", SVC_NAME % "round((probe_ssl_earliest_cert_expiry - time()) / 86400)", "Cert days",
          [("unit", "d"), ("decimals", 0), ("thresholds", CERT_DAYS), CELL_COLOR_TEXT, ("custom.width", 110)]),
         ("H", SVC_NAME % "probe_http_content_length", "Body",
          [("unit", "bytes"), ("decimals", 0), ("noValue", "—")])],
        h=13, join_on="service", keep=r"^(service|Value #.*)$", sort=("Total", True),
        desc="Sorted slowest first. The accepted status codes include 301, 302, 401 and 403 on purpose: "
             "several of these answer a redirect or an auth challenge at the root path, and calling that "
             "an outage would make the panel lie.",
        extra_overrides=[by_name("service", [("displayName", "Service"), ("custom.width", 180)])]))

    g.section("Latency", "Where the time goes on a request through the proxy.")
    g.extend([
        timeseries("Probe duration — eight slowest",
                   [q("topk(8, %s)" % (SVC_NAME % "probe_duration_seconds"), "{{service}}")],
                   unit="s", h=9,
                   desc="Top eight. The table above covers all nineteen."),
        timeseries("Phase breakdown for $service",
                   [q('sum by (phase) (probe_http_duration_seconds{%s})' % svc, "{{phase}}")],
                   unit="s", h=9, stack=True,
                   desc="Resolve, connect, TLS, process, transfer — for whichever services the Service "
                        "dropdown has selected. Stacked, so the height is the whole request."),
    ])

    g.section("TLS", "NPM serves a real wildcard certificate, so verification is on and this number means "
                     "something.")
    g.add(bargauge(
        "Days until the certificate expires",
        [q(SVC_NAME % "(probe_ssl_earliest_cert_expiry - time()) / 86400", "{{service}}", instant=True)],
        w=12, h=11, unit="d", decimals=0, maxv=90, thr=CERT_DAYS,
        desc="All nineteen share one wildcard, so they renew together — a short bar here is a fleet-wide "
             "problem, not one service's."))
    g.add(timeseries(
        "Certificate lifetime remaining",
        [q(SVC_NAME % "(probe_ssl_earliest_cert_expiry - time()) / 86400", "{{service}}")],
        w=12, h=11, unit="d", thr=CERT_DAYS, thr_style="dashed",
        desc="The sawtooth is renewal. A line that keeps descending past 30 days is a renewal that stopped "
             "working."))

    return dashboard(
        "services-uptime", "Services & Uptime", g,
        tags=["homelab", "services"],
        description="Nineteen internal service names, probed end to end through the proxy.",
        refresh="1m", time_from="now-24h",
        templating=[var_query("service", "Service", "label_values(probe_success, instance)")])


# ===================================================== Storage & drive health

def storage():
    g = Grid()
    HV = 'role="hypervisor"'

    g.section("Headroom", "Capacity first, because a full filesystem takes a service down faster than a "
                          "dying disk does.")
    g.extend([
        stat("Fullest filesystem", [q("max(%s)" % inv.fs_used_pct(), instant=True)], w=4,
             unit="percent", decimals=1, thr=PCT_USED, graph="area"),
        stat("Filesystems over 80%",
             [q("count(%s > 80) or vector(0)" % inv.fs_used_pct(), instant=True)], w=4,
             thr=thresholds(("green", None), ("yellow", 1), ("orange", 3))),
        stat("ZFS pools online",
             [q('sum(max by (host, zpool) (node_zfs_zpool_state{state="online",host="grey-server"}))', instant=True)],
             w=4, thr=thresholds(("red", None), ("green", 7)),
             desc="Seven datasets on hddpool-1, on grey-server. Only grey-server has a ZFS pool; the two "
                  "LXC guests that appear to have one are reading its kernel."),
        stat("NVMe critical warnings", [q("sum(nvme_critical_warning) or vector(0)", instant=True)], w=4,
             thr=BAD_ABOVE_ZERO, color_mode="background",
             desc="Any non-zero value is the drive itself asking for attention."),
        stat("Lowest NVMe spare", [q("min(nvme_available_spare_ratio) * 100", instant=True)], w=4,
             unit="percent", decimals=0,
             thr=thresholds(("red", None), ("orange", 10), ("yellow", 30), ("green", 50))),
        stat("SMART self-assessments failing",
             [q("count(smartmon_device_smart_healthy == 0"
                " and on (host, disk) smartmon_device_smart_available == 1) or vector(0)", instant=True)],
             w=4, thr=BAD_ABOVE_ZERO, color_mode="background",
             desc="Only disks that actually report a self-assessment are counted. Both QEMU guests expose a "
                  "virtual disk with none, which is absent rather than failed."),
    ])

    g.section("Filesystems", "Every real mount in the fleet. Pseudo-filesystems are excluded — they say "
                             "nothing about capacity.")
    g.add(joined_table(
        "Filesystem headroom",
        [("A", inv.fs_used_pct(), "Used",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge()),
         ("B", "node_filesystem_avail_bytes{%s}" % FS, "Free", [("unit", "bytes"), ("decimals", 1)]),
         ("C", "node_filesystem_size_bytes{%s}" % FS, "Size", [("unit", "bytes"), ("decimals", 1)]),
         ("D", "100 * (1 - node_filesystem_files_free{%s} / node_filesystem_files{%s})" % (FS, FS), "Inodes",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge()),
         ("E", "predict_linear(node_filesystem_avail_bytes{%s}[6h], 30 * 86400)" % FS, "Free in 30d",
          [("unit", "bytes"), ("decimals", 1), CELL_COLOR_TEXT,
           ("thresholds", thresholds(("red", None), ("orange", 1), ("green", 5e9)))])],
        h=14, join_on="host", keep=r"^(host|mountpoint|device|fstype|Value #.*)$", sort=("Used", True),
        desc="`Free in 30d` extrapolates the last six hours forward a month. It is a straight line through "
             "noisy data, so read it as a direction, not a date — but a negative number there is a mount "
             "worth watching.",
        extra_overrides=[
            by_name("host", [("displayName", "Host"), ("custom.width", 150), HOST_LINK]),
            by_name("mountpoint", [("displayName", "Mount"), ("custom.width", 180)]),
            by_name("device", [("displayName", "Device")]),
            by_name("fstype", [("displayName", "Type"), ("custom.width", 90)])]))
    g.add(timeseries(
        "Filesystem fill — eight tightest",
        [q("topk(8, %s)" % inv.fs_used_pct(), "{{host}} {{mountpoint}}")],
        w=24, h=9, unit="percent", maxv=100, thr=PCT_USED, thr_style="dashed",
        desc="Top eight. The table above covers every mount."))

    g.section("Disk I/O", "Physical devices only. On an LXC guest these are the node's disks, not the "
                          "guest's, because /proc/diskstats is not namespaced.")
    g.extend([
        timeseries("Throughput — eight busiest devices",
                   [q("topk(8, rate(node_disk_read_bytes_total{%s}[$__rate_interval]))" % DISK,
                      "{{host}} {{device}} read"),
                    q("topk(8, rate(node_disk_written_bytes_total{%s}[$__rate_interval]))" % DISK,
                      "{{host}} {{device}} write", ref="B")],
                   unit="Bps", h=9),
        timeseries("Utilisation — eight busiest devices",
                   [q("topk(8, rate(node_disk_io_time_seconds_total{%s}[$__rate_interval]) * 100)" % DISK,
                      "{{host}} {{device}}")],
                   unit="percent", maxv=100, h=9, thr=PCT_LOAD,
                   desc="Share of wall time the device had at least one request in flight. Sustained 100% "
                        "is a saturated disk."),
    ])

    g.section("NVMe", "The four NVMe drives that report SMART data, on purple, blue, red and green.")
    g.add(joined_table(
        "NVMe health",
        [("A", "nvme_critical_warning", "Warning",
          [CELL_COLOR_BG, ("thresholds", BAD_ABOVE_ZERO), ("decimals", 0), ("custom.width", 100)]),
         ("B", "nvme_temperature_celsius * 9 / 5 + 32", "Temp",
          [("unit", "fahrenheit"), ("decimals", 0), ("thresholds", TEMP_F), CELL_COLOR_TEXT]),
         ("C", "nvme_available_spare_ratio * 100", "Spare",
          [("unit", "percent"), ("decimals", 0),
           ("thresholds", thresholds(("red", None), ("orange", 10), ("green", 30)))] + cell_gauge()),
         ("D", "nvme_percentage_used_ratio * 100", "Endurance used",
          [("unit", "percent"), ("decimals", 0), ("thresholds", PCT_USED)] + cell_gauge()),
         ("E", "nvme_power_on_hours_total", "Powered on", [("unit", "h"), ("decimals", 0)]),
         ("F", "nvme_media_errors_total", "Media errors",
          [("decimals", 0), CELL_COLOR_TEXT, ("thresholds", BAD_ABOVE_ZERO)]),
         ("G", "nvme_unsafe_shutdowns_total", "Unsafe stops", [("decimals", 0)]),
         ("H", "nvme_data_units_written_total * 512 * 1000", "Written",
          [("unit", "bytes"), ("decimals", 1)])],
        w=24, h=8, join_on="host", keep=r"^(host|device|Value #.*)$", sort=("Endurance used", True),
        desc="`Written` converts the NVMe data-unit counter, which counts 1000 × 512-byte units.",
        extra_overrides=[by_name("host", [("displayName", "Host"), ("custom.width", 160), HOST_LINK]),
                         by_name("device", [("displayName", "Device"), ("custom.width", 120)])]))
    g.extend([
        timeseries("NVMe temperature", [q("nvme_temperature_celsius * 9 / 5 + 32", "{{host}} {{device}}")],
                   unit="fahrenheit", h=9, thr=TEMP_F, thr_style="dashed", min_zero=False),
        bargauge("Endurance used", [q("nvme_percentage_used_ratio * 100", "{{host}} {{device}}", instant=True)],
                 h=9, desc="The drive's own wear estimate. 100% means it has written its rated endurance, "
                           "not that it has failed."),
    ])

    g.section("SATA drives", "The four spinning and SATA-SSD drives that report a SMART self-assessment.")
    g.add(joined_table(
        "SMART",
        [("A", "smartmon_device_smart_healthy and on (host, disk) smartmon_device_smart_available == 1", "Healthy",
          [CELL_COLOR_BG, ("mappings", mapping({0: ("FAILING", "red"), 1: ("PASSED", "green")})),
           ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 100)]),
         ("B", "(smartmon_temperature_celsius_raw_value"
               " or smartmon_airflow_temperature_cel_raw_value) * 9 / 5 + 32", "Temp",
          [("unit", "fahrenheit"), ("decimals", 0), ("thresholds", TEMP_F), CELL_COLOR_TEXT]),
         ("C", "smartmon_power_on_hours_raw_value", "Powered on", [("unit", "h"), ("decimals", 0)]),
         ("D", "smartmon_power_cycle_count_raw_value", "Power cycles", [("decimals", 0)]),
         ("E", "smartmon_reallocated_sector_ct_raw_value", "Reallocated",
          [("decimals", 0), CELL_COLOR_TEXT, ("thresholds", BAD_ABOVE_ZERO)]),
         ("F", "smartmon_current_pending_sector_raw_value", "Pending",
          [("decimals", 0), CELL_COLOR_TEXT, ("thresholds", BAD_ABOVE_ZERO)]),
         ("G", "smartmon_udma_crc_error_count_raw_value", "CRC errors",
          [("decimals", 0), CELL_COLOR_TEXT, ("thresholds", BAD_ABOVE_ZERO)])],
        w=24, h=8, join_on="host", keep=r"^(host|disk|Value #.*)$", sort=("Powered on", True),
        desc="Reallocated, pending and CRC counts are the three that matter: any of them climbing is a "
             "drive on the way out, whatever the overall assessment still says.",
        extra_overrides=[by_name("host", [("displayName", "Host"), ("custom.width", 160), HOST_LINK]),
                         by_name("disk", [("displayName", "Disk"), ("custom.width", 120)])]))

    g.section("ZFS", "hddpool-1 on grey-server, the fleet's only ZFS pool.")
    g.extend([
        stat("Pool state",
             [q('max(node_zfs_zpool_state{state="online",host="grey-server"})', instant=True)], w=8, h=6,
             mappings=mapping({0: ("NOT ONLINE", "red"), 1: ("ONLINE", "green")}),
             thr=GOOD_ABOVE_ZERO, color_mode="background", text_mode="value"),
        timeseries("ARC size", [q('node_zfs_arc_size{host="grey-server"}', "arc")],
                   w=8, h=6, unit="bytes",
                   desc="The adaptive replacement cache, in RAM. It grows to fill what it is allowed."),
        timeseries("ARC hit ratio",
                   [q('100 * rate(node_zfs_arc_hits{host="grey-server"}[$__rate_interval])'
                      ' / clamp_min(rate(node_zfs_arc_hits{host="grey-server"}[$__rate_interval])'
                      ' + rate(node_zfs_arc_misses{host="grey-server"}[$__rate_interval]), 1)', "hit ratio")],
                   w=8, h=6, unit="percent", maxv=100,
                   thr=thresholds(("red", None), ("orange", 80), ("green", 95)),
                   desc="Clamped so an idle pool reads 0 rather than dividing by zero."),
    ])

    return dashboard(
        "storage-health", "Storage & Drive Health", g,
        tags=["homelab", "storage"],
        description="Capacity first, then the drives underneath it: NVMe, SATA SMART, and ZFS.",
        refresh="1m", time_from="now-24h")


# ==================================================================== Network

def network():
    g = Grid()

    g.section("Right now", "Physical and bridge interfaces only. A Docker host carries a veth per container "
                           "and a Proxmox node three interfaces per guest; grey-server has 39 interfaces, "
                           "of which six mean anything.")
    g.extend([
        stat("Fleet inbound",
             [q("sum(rate(node_network_receive_bytes_total{%s}[$__rate_interval]))" % NET, instant=True)],
             w=4, unit="Bps", decimals=1, color_mode="none", graph="area"),
        stat("Fleet outbound",
             [q("sum(rate(node_network_transmit_bytes_total{%s}[$__rate_interval]))" % NET, instant=True)],
             w=4, unit="Bps", decimals=1, color_mode="none", graph="area"),
        stat("Interfaces down",
             [q("count(node_network_up{%s} == 0) or vector(0)" % NET, instant=True)], w=4,
             thr=thresholds(("green", None), ("yellow", 1)),
             desc="A configured interface with no carrier. On a Proxmox node a spare NIC sits here "
                  "permanently and is not a fault."),
        stat("Errors and drops, last hour",
             [q("sum(increase(node_network_receive_errs_total{%s}[1h]))"
                " + sum(increase(node_network_transmit_errs_total{%s}[1h]))"
                " + sum(increase(node_network_receive_drop_total{%s}[1h]))"
                " + sum(increase(node_network_transmit_drop_total{%s}[1h])) or vector(0)" % (NET, NET, NET, NET),
                instant=True)],
             w=4, decimals=0, thr=thresholds(("green", None), ("yellow", 1), ("orange", 100))),
        stat("Busiest conntrack table",
             [q("max(node_nf_conntrack_entries / node_nf_conntrack_entries_limit * 100)", instant=True)],
             w=4, unit="percent", decimals=1, thr=PCT_USED,
             desc="Filling this table drops new connections silently."),
        stat("TCP retransmit rate",
             [q("sum(rate(node_netstat_Tcp_RetransSegs[$__rate_interval]))", instant=True)],
             w=4, unit="pps", decimals=2, thr=thresholds(("green", None), ("yellow", 10), ("orange", 100)),
             desc="Segments resent per second across the fleet. Sustained non-zero means loss somewhere."),
    ])

    g.section("Throughput", "Who is moving bytes.")
    g.extend([
        timeseries("Inbound — eight busiest hosts",
                   [q("topk(8, sum by (host) (rate(node_network_receive_bytes_total{%s}[$__rate_interval])))" % NET,
                      "{{host}}")], unit="Bps", h=9,
                   desc="Top eight. The table below covers all eighteen."),
        timeseries("Outbound — eight busiest hosts",
                   [q("topk(8, sum by (host) (rate(node_network_transmit_bytes_total{%s}[$__rate_interval])))" % NET,
                      "{{host}}")], unit="Bps", h=9,
                   desc="Top eight. The table below covers all eighteen."),
    ])
    g.add(joined_table(
        "Per host",
        [("A", "sum by (host) (rate(node_network_receive_bytes_total{%s}[$__rate_interval]))" % NET, "In",
          [("unit", "Bps"), ("decimals", 1)]),
         ("B", "sum by (host) (rate(node_network_transmit_bytes_total{%s}[$__rate_interval]))" % NET, "Out",
          [("unit", "Bps"), ("decimals", 1)]),
         ("C", "sum by (host) (increase(node_network_receive_bytes_total{%s}[24h]))" % NET, "In, 24h",
          [("unit", "bytes"), ("decimals", 1)]),
         ("D", "sum by (host) (increase(node_network_transmit_bytes_total{%s}[24h]))" % NET, "Out, 24h",
          [("unit", "bytes"), ("decimals", 1)]),
         ("E", "sum by (host) (node_netstat_Tcp_CurrEstab)", "TCP open", [("decimals", 0)]),
         ("F", "sum by (host) (rate(node_netstat_Tcp_RetransSegs[$__rate_interval]))", "Retrans/s",
          [("unit", "pps"), ("decimals", 2), CELL_COLOR_TEXT,
           ("thresholds", thresholds(("green", None), ("yellow", 1), ("orange", 20)))]),
         ("G", "max by (host) (node_nf_conntrack_entries / node_nf_conntrack_entries_limit * 100)", "Conntrack",
          [("unit", "percent"), ("decimals", 2), ("thresholds", PCT_USED), ("noValue", "—")] + cell_gauge())],
        h=12, sort=("In", True),
        extra_overrides=[by_name("host", [("displayName", "Host"), ("custom.width", 160), HOST_LINK]),
                         by_name("role", [("displayName", "Role"), ("custom.width", 120)])]))

    g.section("Errors and drops", "This table is empty when the fleet is clean.")
    g.add(empty_ok(table(
        "Interfaces dropping or erroring, last hour",
        [tq("sum by (host, device) ("
            "increase(node_network_receive_errs_total{%s}[1h])"
            " + increase(node_network_transmit_errs_total{%s}[1h])"
            " + increase(node_network_receive_drop_total{%s}[1h])"
            " + increase(node_network_transmit_drop_total{%s}[1h])) > 0" % (NET, NET, NET, NET))],
        w=12, h=9, no_value="No interface has dropped or errored a packet in the last hour.",
        desc="Errors and drops summed. A bridge dropping packets it was never meant to forward is normal; "
             "a physical NIC erroring is not.",
        transformations=[
            {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(host|device|Value)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                {"host": "Host", "device": "Interface", "Value": "Packets"},
             "indexByName": {"host": 0, "device": 1, "Value": 2}}}],
        sort=("Packets", True),
        overrides=[by_name("Packets", [("decimals", 0), CELL_COLOR_TEXT,
                                       ("thresholds", thresholds(("yellow", None), ("orange", 100), ("red", 10000)))])])))
    g.add(timeseries(
        "Drops per second — eight worst interfaces",
        [q("topk(8, sum by (host, device) ("
           "rate(node_network_receive_drop_total{%s}[$__rate_interval])"
           " + rate(node_network_transmit_drop_total{%s}[$__rate_interval])))" % (NET, NET),
           "{{host}} {{device}}")],
        w=12, h=9, unit="pps", thr=thresholds(("green", None), ("orange", 1))))

    g.section("TCP and connection tracking", "State the fleet is holding, rather than bytes moving.")
    g.extend([
        timeseries("Established connections",
                   [q("topk(8, sum by (host) (node_netstat_Tcp_CurrEstab))", "{{host}}")], h=9),
        timeseries("Retransmitted segments",
                   [q("topk(8, sum by (host) (rate(node_netstat_Tcp_RetransSegs[$__rate_interval])))", "{{host}}")],
                   unit="pps", h=9, thr=thresholds(("green", None), ("yellow", 1), ("orange", 20))),
        bargauge("Conntrack table used",
                 [q("node_nf_conntrack_entries / node_nf_conntrack_entries_limit * 100", "{{host}}", instant=True)],
                 w=12, h=9, desc="Reported by seventeen hosts; the eighteenth has no conntrack module loaded."),
        timeseries("Sockets in use",
                   [q("topk(8, node_sockstat_TCP_inuse)", "{{host}} TCP"),
                    q("topk(8, node_sockstat_UDP_inuse)", "{{host}} UDP", ref="B")],
                   w=12, h=9),
    ])

    return dashboard(
        "network", "Network", g,
        tags=["homelab", "network"],
        description="Host-side networking: throughput, errors, TCP state and connection tracking. The "
                    "switches and access points are not in here — that needs a UniFi exporter.",
        refresh="30s", time_from="now-6h")


# ================================================================ Power / UPS

# nut_load and nut_battery_charge are ratios in the range 0..1, not percentages.
# Multiplying by the nominal VA rating turns load into watts: 0.27 x 900 = 243 W.
def power():
    g = Grid()
    ups = 'ups=~"$ups"'

    g.section("Right now", "Two APC Back-UPS Pro BR1500MS2 units, read over NUT. ups01 carries red-server, "
                           "ups02 carries grey-server.")
    g.extend([
        stat("Mains", [q('nut_ups_status{status="OL", %s}' % ups, "{{ups}}", instant=True)], w=4,
             mappings=mapping({0: ("ON BATTERY", "red"), 1: ("ON MAINS", "green")}),
             thr=GOOD_ABOVE_ZERO, color_mode="background", text_mode="value_and_name"),
        stat("Battery charge", [q("nut_battery_charge{%s} * 100" % ups, "{{ups}}", instant=True)], w=4,
             unit="percent", decimals=0, maxv=100,
             thr=thresholds(("red", None), ("orange", 30), ("yellow", 60), ("green", 90)),
             text_mode="value_and_name"),
        stat("Runtime left", [q("nut_battery_runtime_seconds{%s}" % ups, "{{ups}}", instant=True)], w=4,
             unit="s", decimals=0,
             thr=thresholds(("red", None), ("orange", 300), ("yellow", 900), ("green", 1800)),
             text_mode="value_and_name"),
        stat("Load", [q("nut_load{%s} * 100" % ups, "{{ups}}", instant=True)], w=4,
             unit="percent", decimals=0, maxv=100, thr=PCT_LOAD, text_mode="value_and_name"),
        stat("Draw", [q("nut_load{%s} * nut_real_power_nominal_watts{%s}" % (ups, ups), "{{ups}}", instant=True)],
             w=4, unit="watt", decimals=0, color_mode="none", graph="area", text_mode="value_and_name",
             desc="Load as a share of the 900 W nominal rating. NUT reports no true wattage on this model, "
                  "so this is an estimate the UPS derives, not a meter reading."),
        stat("Input voltage", [q("nut_input_voltage_volts{%s}" % ups, "{{ups}}", instant=True)], w=4,
             unit="volt", decimals=0, text_mode="value_and_name",
             thr=thresholds(("red", None), ("orange", 100), ("green", 110), ("orange", 130), ("red", 140))),
    ])

    g.section("Battery", "How long you have, and whether it is getting shorter.")
    g.extend([
        bargauge("Charge", [q("nut_battery_charge{%s} * 100" % ups, "{{ups}}", instant=True)],
                 w=12, h=7, thr=thresholds(("red", None), ("orange", 30), ("yellow", 60), ("green", 90))),
        bargauge("Runtime remaining", [q("nut_battery_runtime_seconds{%s}" % ups, "{{ups}}", instant=True)],
                 w=12, h=7, unit="s", maxv=3600, decimals=0,
                 thr=thresholds(("red", None), ("orange", 300), ("yellow", 900), ("green", 1800)),
                 desc="Scaled to an hour. The low-battery shutdown trigger on both units is 120 seconds."),
        timeseries("Charge over time", [q("nut_battery_charge{%s} * 100" % ups, "{{ups}}")],
                   w=12, h=9, unit="percent", maxv=100),
        timeseries("Runtime over time", [q("nut_battery_runtime_seconds{%s}" % ups, "{{ups}}")],
                   w=12, h=9, unit="s",
                   desc="A runtime estimate that keeps falling at the same load is a battery losing capacity."),
        timeseries("Battery voltage", [q("nut_battery_voltage_volts{%s}" % ups, "{{ups}}")],
                   w=24, h=8, unit="volt", min_zero=False,
                   desc="Nominal is 24 V. A resting pack well under that is worn; a spike above it is charging."),
    ])

    g.section("Load and mains", "What the units are carrying, and what the wall is giving them.")
    g.extend([
        bargauge("Load", [q("nut_load{%s} * 100" % ups, "{{ups}}", instant=True)], w=12, h=7, thr=PCT_LOAD),
        bargauge("Estimated draw",
                 [q("nut_load{%s} * nut_real_power_nominal_watts{%s}" % (ups, ups), "{{ups}}", instant=True)],
                 w=12, h=7, unit="watt", maxv=900, decimals=0, thr=PCT_LOAD),
        timeseries("Load over time", [q("nut_load{%s} * 100" % ups, "{{ups}}")],
                   w=12, h=9, unit="percent", maxv=100, thr=PCT_LOAD),
        timeseries("Input voltage",
                   [q("nut_input_voltage_volts{%s}" % ups, "{{ups}}"),
                    q("nut_input_transfer_low_volts{%s}" % ups, "{{ups}} transfer low", ref="B"),
                    q("nut_input_transfer_high_volts{%s}" % ups, "{{ups}} transfer high", ref="C")],
                   w=12, h=9, unit="volt", min_zero=False,
                   desc="The two flat lines are the thresholds at which the unit switches to battery: 88 V "
                        "and 144 V. Mains sagging toward either is what drains a battery without an outage.",
                   overrides=[by_regex(".*transfer.*", [("custom.lineStyle", {"fill": "dash", "dash": [8, 6]}),
                                                        ("custom.lineWidth", 1),
                                                        ("color", fixed("text"))])]),
    ])

    g.section("Status history", "Every flag NUT reports, over time.")
    g.add(state_timeline(
        "UPS status flags", [q("nut_ups_status{%s} == 1" % ups, "{{ups}} {{status}}")], h=9,
        mappings=mapping({1: ("set", "green")}), legend=LEGEND_LIST,
        desc="A band appears only while its flag is set. OL is on line. OB is on battery, LB is low "
             "battery, CHRG is charging, RB means replace battery."))
    g.add(joined_table(
        "Unit facts",
        [("A", "nut_real_power_nominal_watts{%s}" % ups, "Nominal", [("unit", "watt"), ("decimals", 0)]),
         ("B", "nut_battery_voltage_nominal_volts{%s}" % ups, "Battery nominal",
          [("unit", "volt"), ("decimals", 0)]),
         ("C", "nut_input_voltage_nominal_volts{%s}" % ups, "Input nominal", [("unit", "volt"), ("decimals", 0)]),
         ("D", "nut_battery_charge_low{%s} * 100" % ups, "Low-battery at", [("unit", "percent"), ("decimals", 0)]),
         ("E", "nut_battery_runtime_low_seconds{%s}" % ups, "Shutdown at", [("unit", "s"), ("decimals", 0)]),
         ("F", "nut_delay_shutdown_seconds{%s}" % ups, "Shutdown delay", [("unit", "s"), ("decimals", 0)]),
         ("G", "nut_beeper_status{%s}" % ups, "Beeper",
          [("mappings", mapping({0: ("disabled", "text"), 1: ("enabled", "text")})), ("custom.width", 100)])],
        h=7, join_on="ups", keep=r"^(ups|host|Value #.*)$",
        extra_overrides=[by_name("ups", [("displayName", "UPS"), ("custom.width", 100)]),
                         by_name("host", [("displayName", "Read from"), ("custom.width", 160), HOST_LINK])]))

    return dashboard(
        "power-ups", "Power & UPS", g,
        tags=["homelab", "power"],
        description="Both APC units over the NUT protocol. Load and charge arrive as ratios and are scaled "
                    "to percentages here.",
        refresh="1m", time_from="now-24h",
        templating=[var_query("ups", "UPS", "label_values(nut_status, ups)")])


# ========================================================== Monitoring health

def monitoring():
    g = Grid()

    g.section("Scraping", "Whether the thing that watches everything else is itself working.")
    g.extend([
        stat("Targets up", [q("count(up == 1)", instant=True)], w=4, color_mode="none", graph="area"),
        stat("Targets down", [q("count(up == 0) or vector(0)", instant=True)], w=4,
             thr=BAD_ABOVE_ZERO, color_mode="background"),
        stat("Slowest scrape", [q("max(scrape_duration_seconds)", instant=True)], w=4,
             unit="s", decimals=2, graph="area",
             thr=thresholds(("green", None), ("yellow", 1), ("orange", 5), ("red", 10)),
             desc="A scrape slower than its interval is a target about to start missing samples."),
        stat("Samples ingested",
             [q("sum(rate(prometheus_tsdb_head_samples_appended_total[$__rate_interval]))", instant=True)],
             w=4, unit="wps", decimals=0, color_mode="none", graph="area"),
        stat("Active series", [q("prometheus_tsdb_head_series", instant=True)], w=4,
             decimals=0, color_mode="none", graph="area",
             thr=thresholds(("green", None), ("yellow", 500000), ("orange", 1000000))),
        stat("TSDB on disk", [q("sum(prometheus_tsdb_storage_blocks_bytes)", instant=True)], w=4,
             unit="bytes", decimals=1, color_mode="none", graph="area",
             desc="Compacted blocks only, so it lags the head block by up to two hours. Retention is 15 days."),
    ])

    g.section("Targets", "Every scrape endpoint, its health and what it costs.")
    g.add(joined_table(
        "Scrape targets",
        [("A", "up", "Up",
          [CELL_COLOR_BG, ("mappings", MAP_UP_DOWN), ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 70)]),
         ("B", "scrape_duration_seconds", "Duration",
          [("unit", "s"), ("decimals", 3),
           ("thresholds", thresholds(("green", None), ("yellow", 1), ("orange", 5)))] + cell_gauge(0, 5)),
         ("C", "scrape_samples_scraped", "Samples", [("decimals", 0)]),
         ("D", "scrape_series_added", "New series",
          [("decimals", 0), CELL_COLOR_TEXT,
           ("thresholds", thresholds(("green", None), ("yellow", 100), ("orange", 1000)))]),
         ("E", "scrape_samples_post_metric_relabeling", "Kept", [("decimals", 0)])],
        h=16, join_on="instance", keep=r"^(instance|job|host|Value #.*)$", sort=("Duration", True),
        desc="Sorted slowest first. `New series` climbing on every scrape is a cardinality leak — a label "
             "carrying something that changes each time.",
        extra_overrides=[by_name("instance", [("displayName", "Target"), ("custom.width", 260)]),
                         by_name("job", [("displayName", "Job"), ("custom.width", 120)]),
                         by_name("host", [("displayName", "Host"), ("custom.width", 150), HOST_LINK])]))
    g.extend([
        timeseries("Scrape duration by job",
                   [q("max by (job) (scrape_duration_seconds)", "{{job}}")], h=9, unit="s",
                   desc="The slowest target in each job."),
        timeseries("Samples scraped by job",
                   [q("sum by (job) (scrape_samples_scraped)", "{{job}}")], h=9, stack=True,
                   desc="Stacked, so the height is what one full scrape cycle costs."),
    ])

    g.section("Storage", "How the time series database is holding up.")
    g.extend([
        timeseries("Active series", [q("prometheus_tsdb_head_series", "head series")], h=9, w=8),
        timeseries("Ingestion rate",
                   [q("rate(prometheus_tsdb_head_samples_appended_total[$__rate_interval])", "samples/s")],
                   h=9, w=8, unit="wps"),
        timeseries("Block storage",
                   [q("prometheus_tsdb_storage_blocks_bytes", "on disk")], h=9, w=8, unit="bytes"),
        timeseries("Compactions and truncations",
                   [q("increase(prometheus_tsdb_compactions_total[$__interval])", "compactions"),
                    q("increase(prometheus_tsdb_wal_truncations_total[$__interval])", "WAL truncations", ref="B")],
                   h=8, w=12, decimals=0,
                   desc="Both are routine housekeeping. Compactions failing, rather than running, is the "
                        "thing worth noticing."),
        timeseries("Query duration",
                   [q("prometheus_engine_query_duration_seconds{quantile=\"0.99\"}", "{{slice}} p99")],
                   h=8, w=12, unit="s",
                   desc="p99 by stage. A slow eval stage is usually one dashboard asking for too much."),
    ])

    g.section("Exporters", "The 18 node_exporters, and the things they quietly fail to collect.")
    g.add(joined_table(
        "node_exporter fleet",
        [("A", 'max by (host) (up{job="node"})', "Up",
          [CELL_COLOR_BG, ("mappings", MAP_UP_DOWN), ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 70)]),
         ("B", "max by (host, version) (node_exporter_build_info)", "Version", [("custom.width", 110)]),
         ("C", 'max by (host) (scrape_duration_seconds{job="node"})', "Scrape",
          [("unit", "s"), ("decimals", 3)] + cell_gauge(0, 2)),
         ("D", "count by (host) (node_scrape_collector_success == 0)", "Collectors erroring",
          [("decimals", 0), CELL_COLOR_TEXT, ("noValue", "0"),
           ("thresholds", thresholds(("green", None), ("yellow", 1)))]),
         ("E", "max by (host) (abs(node_timex_offset_seconds))", "Clock offset",
          [("unit", "s"), ("decimals", 6), CELL_COLOR_TEXT,
           ("thresholds", thresholds(("green", None), ("yellow", 0.05), ("orange", 0.5)))]),
         ("F", "count by (host) (node_systemd_unit_state{state=\"failed\"} == 1)", "Failed units",
          [("decimals", 0), CELL_COLOR_TEXT, ("noValue", "0"), ("thresholds", thresholds(("green", None), ("orange", 1)))]),
         ("G", "max by (host) (apt_upgrades_pending)", "Updates",
          [("decimals", 0), ("noValue", "—"), CELL_COLOR_TEXT,
           ("thresholds", thresholds(("green", None), ("yellow", 1), ("orange", 20)))])],
        h=14, sort=("Collectors erroring", True),
        desc="`Collectors erroring` is almost always hardware the host does not have — fibrechannel, "
             "infiniband, tape, IPVS. It is worth reading once to learn the baseline, not worth alerting on. "
             "`Version` is 1.9.0 fleet-wide because APT owns the binary.",
        extra_overrides=[by_name("host", [("displayName", "Host"), ("custom.width", 160), HOST_LINK]),
                         by_name("version", [("displayName", "Version"), ("custom.width", 110)]),
                         by_name("role", [("displayName", "Role"), ("custom.width", 120)])]))
    g.add(empty_ok(table(
        "Failed systemd units",
        [tq('node_systemd_unit_state{state="failed"} == 1')],
        w=12, h=9, no_value="No unit is in the failed state anywhere in the fleet.",
        transformations=[
            {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(host|name)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName": {"host": "Host", "name": "Unit"},
                                           "indexByName": {"host": 0, "name": 1}}}],
        overrides=[by_name("Host", [("custom.width", 170), HOST_LINK])])))
    g.add(empty_ok(table(
        "Textfile collector errors",
        [tq("node_textfile_scrape_error != 0")],
        w=12, h=9, no_value="Every textfile collector parsed cleanly.",
        desc="The TeamSpeak and SMART metrics arrive this way. An error here means a half-written file, "
             "so the metrics above it are stale rather than absent — which is the more dangerous failure.",
        transformations=[
            {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(host|Value)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName": {"host": "Host", "Value": "Error"},
                                           "indexByName": {"host": 0, "Value": 1}}}],
        overrides=[by_name("Host", [("custom.width", 170), HOST_LINK])])))
    g.add(empty_ok(table(
        "Pending package updates",
        [tq("apt_upgrades_pending > 0")],
        w=24, h=9, no_value="No host is reporting a pending update.",
        desc="Only the Debian hosts run the APT collector; Rocky and the two hosts on an upstream binary "
             "are absent by design rather than up to date.",
        transformations=[
            {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(host|origin|arch|Value)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                {"host": "Host", "origin": "Origin", "arch": "Arch", "Value": "Pending"},
             "indexByName": {"host": 0, "origin": 1, "arch": 2, "Value": 3}}}],
        sort=("Pending", True),
        overrides=[by_name("Host", [("custom.width", 170), HOST_LINK]),
                   by_name("Pending", [("decimals", 0), CELL_COLOR_TEXT,
                                       ("thresholds", thresholds(("yellow", None), ("orange", 20)))])])))

    return dashboard(
        "monitoring-health", "Monitoring Health", g,
        tags=["homelab", "monitoring"],
        description="Prometheus watching itself: target health, scrape cost, TSDB growth, and the state of "
                    "the 18 node_exporters.",
        refresh="1m", time_from="now-6h")


# ================================================================== TeamSpeak

def teamspeak():
    g = Grid()
    s = 'server=~"$server"'

    g.section(
        "Right now",
        "Two voice servers on alpha-prod-01, each probed twice a minute: once at the public address a "
        "person types, and once at its local UDP port on the host. The pair is the whole point — local up "
        "with public down is the tunnel or DNS, not TeamSpeak.")
    g.extend([
        stat("Verdict", [q("teamspeak_server_fault{%s} * 2 + teamspeak_tunnel_fault{%s}" % (s, s),
                           "{{server}}", instant=True)], w=8, h=5,
             mappings=mapping({0: ("SERVING", "green"), 1: ("PUBLIC PATH DOWN", "orange"),
                               2: ("VOICE DOWN", "red"), 3: ("VOICE DOWN", "red")}),
             thr=thresholds(("green", None), ("orange", 1), ("red", 2)),
             color_mode="background", text_mode="value_and_name",
             desc="PUBLIC PATH DOWN covers three different faults: the Playit relay is unreachable, the SRV "
                  "record is wrong, or the collector cannot resolve DNS at all. The three stats to the right "
                  "tell them apart — check Name resolution first."),
        stat("Public address", [q("teamspeak_public_up{%s}" % s, "{{server}}", instant=True)], w=8, h=5,
             mappings=MAP_UP_DOWN, thr=GOOD_ABOVE_ZERO, color_mode="background",
             text_mode="value_and_name",
             desc="A real TeamSpeak Init1 handshake through the Playit relay, so UP means the voice service "
                  "answered rather than a port merely being open."),
        stat("Local voice", [q("teamspeak_local_up{%s}" % s, "{{server}}", instant=True)], w=8, h=5,
             mappings=MAP_UP_DOWN, thr=GOOD_ABOVE_ZERO, color_mode="background",
             text_mode="value_and_name",
             desc="The same handshake against 127.0.0.1 on the host. Down here means TeamSpeak itself."),
        stat("Name resolution", [q("teamspeak_dns_srv_up{%s}" % s, "{{server}}", instant=True)], w=8, h=5,
             mappings=mapping({0: ("CANNOT RESOLVE", "red"), 1: ("RESOLVES", "green")}),
             thr=GOOD_ABOVE_ZERO, color_mode="background", text_mode="value_and_name",
             desc="Whether the collector could read the _ts3._udp SRV record. When this is red the public "
                  "probe never ran, so the public panels are reporting the monitoring's own blindness rather "
                  "than an outage. That is exactly what happened between 2026-08-10 and 2026-08-27."),
        stat("ServerQuery", [q("teamspeak_query_up{%s}" % s, "{{server}}", instant=True)], w=8, h=5,
             mappings=MAP_OK_FAIL, thr=GOOD_ABOVE_ZERO, color_mode="background",
             text_mode="value_and_name",
             desc="The administrative login. It is how the client and channel counts below are read."),
        stat("Collector freshness", [q("time() - teamspeak_last_probe_timestamp_seconds", instant=True)],
             w=8, h=5, unit="s", decimals=0,
             thr=thresholds(("green", None), ("yellow", 120), ("orange", 300), ("red", 900)),
             desc="Age of the last completed collection. The collector runs every 60 seconds, so anything "
                  "past two minutes means it has stopped and every panel here is stale."),
    ])

    g.section("Availability over time", "Public and local, side by side. They should move together.")
    g.add(state_timeline(
        "Reachability",
        [q("teamspeak_public_up{%s}" % s, "{{server}} public"),
         q("teamspeak_local_up{%s}" % s, "{{server}} local", ref="B"),
         q("teamspeak_dns_srv_up{%s}" % s, "{{server}} SRV record", ref="C")],
        h=9, mappings=mapping({0: ("down", "red"), 1: ("up", "green")}), legend=LEGEND_LIST,
        desc="Three bands per server. Local green with public red is a tunnel or DNS problem; all three red "
             "at once is the host."))
    g.extend([
        stat("Public availability over the selected range",
             [q("avg_over_time(teamspeak_public_up{%s}[$__range]) * 100" % s, "{{server}}", instant=True)],
             w=8, h=7, unit="percent", decimals=3,
             thr=thresholds(("red", None), ("orange", 99), ("yellow", 99.9), ("green", 99.99)),
             text_mode="value_and_name", graph="area"),
        timeseries("Public round trip",
                   [q("teamspeak_public_rtt_seconds{%s} > 0" % s, "{{server}}")],
                   w=16, h=7, unit="s", decimals=3,
                   thr=thresholds(("green", None), ("yellow", 0.15), ("orange", 0.3)),
                   desc="Filtered to non-zero, because a failed probe records zero rather than a time and a "
                        "flat zero line would read as an instant response."),
    ])

    g.section("The public path", "What the SRV record currently points at.")
    g.add(table(
        "Relay endpoints",
        [tq("teamspeak_public_up{%s}" % s)],
        h=6,
        desc="The relay label is written by the collector from the live SRV record on every cycle, so a "
             "Playit port rotation shows up here without an edit. `unresolved:0` means the lookup failed.",
        transformations=[
            {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(server|address|relay|Value)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                {"server": "Server", "address": "Public address", "relay": "Relay", "Value": "Up"},
             "indexByName": {"server": 0, "address": 1, "relay": 2, "Value": 3}}}],
        overrides=[by_name("Up", [CELL_COLOR_BG, ("mappings", MAP_UP_DOWN),
                                  ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 80)]),
                   by_name("Relay", [CELL_COLOR_TEXT,
                                     ("mappings", [{"type": "regex", "options": {"pattern": "^unresolved.*",
                                                                                 "result": {"text": "unresolved — DNS failed",
                                                                                            "color": "red", "index": 0}}}])])]))

    g.section("Server statistics", "Read over ServerQuery, so these go blank if that login stops working.")
    g.extend([
        stat("Clients online", [q("teamspeak_clients_online{%s}" % s, "{{server}}", instant=True)],
             w=6, h=5, color_mode="none", graph="area", text_mode="value_and_name"),
        stat("Channels", [q("teamspeak_channels_online{%s}" % s, "{{server}}", instant=True)],
             w=6, h=5, color_mode="none", text_mode="value_and_name"),
        stat("Slots", [q("teamspeak_max_clients{%s}" % s, "{{server}}", instant=True)],
             w=6, h=5, color_mode="none", text_mode="value_and_name"),
        stat("Virtual server uptime", [q("teamspeak_uptime_seconds{%s}" % s, "{{server}}", instant=True)],
             w=6, h=5, unit="s", decimals=0, color_mode="none", text_mode="value_and_name"),
        timeseries("Clients online", [q("teamspeak_clients_online{%s}" % s, "{{server}}")],
                   w=24, h=9, decimals=0,
                   desc="The two servers are separate virtual servers, not a cluster, so these counts do "
                        "not add up to anything meaningful together."),
    ])

    g.section("Collector", "The exporter itself, which is a textfile written on alpha-prod-01 rather than a "
                           "scrape target.")
    g.extend([
        timeseries("Collection duration", [q("teamspeak_probe_duration_seconds", "duration")],
                   w=12, h=8, unit="s", decimals=2,
                   desc="One cycle probes both servers twice each plus two SRV lookups. Two seconds is "
                        "normal; a jump to the timeout ceiling means a probe is hanging."),
        timeseries("Local round trip", [q("teamspeak_local_rtt_seconds{%s} > 0" % s, "{{server}}")],
                   w=12, h=8, unit="s", decimals=4,
                   desc="Loopback, so this is sub-millisecond whenever TeamSpeak is answering at all."),
    ])

    return dashboard(
        "teamspeak", "TeamSpeak", g,
        tags=["homelab", "teamspeak"],
        description="Voice reachability for ts02 and ts03, public and local, with the fault isolated to "
                    "either the server or the path in front of it.",
        refresh="1m", time_from="now-24h",
        templating=[var_query("server", "Server", "label_values(teamspeak_local_up, server)")])


# ========================================================== One node, one board

def node_dashboard(n: dict) -> dict:
    host = n["host"]
    H = 'host="%s"' % host
    kind = n["kind"]
    g = Grid()

    where = inv.WHAT_IS_IT[kind]
    if n.get("pve"):
        where += ", on [%s](/d/node-%s)" % (n["pve"], n["pve"])
    identity = ("**%s** · `%s` · role `%s` · %s.  \nEight tiles, then one section per resource. "
                "Use **Nodes** in the header to jump to another host."
                % (host, n["ip"], n["role"], where))

    g.section("Status", identity)
    tiles = [
        stat("Reachable", [q('up{job="node", %s}' % H, instant=True)], w=6,
             mappings=MAP_UP_DOWN, thr=GOOD_ABOVE_ZERO, color_mode="background", text_mode="value",
             desc="Whether Prometheus got a scrape, which is not the same as the workload being healthy."),
        stat("Uptime", [q("time() - node_boot_time_seconds{%s}" % H, instant=True)], w=6,
             unit="s", decimals=0, color_mode="none"),
        stat("CPU busy", [q(inv.CPU_BUSY % (", " + H), instant=True)], w=6,
             unit="percent", decimals=1, thr=PCT_LOAD, graph="area"),
        stat("Load per core",
             [q("node_load1{%s} / on (host) group_left () count by (host) "
                "(count by (host, cpu) (node_cpu_seconds_total{%s}))" % (H, H), instant=True)], w=6,
             decimals=2, thr=LOAD_PER_CORE, graph="area",
             desc="Runnable processes divided by cores. Above 1 means work is queueing."),
        stat("Memory used", [q(inv.MEM_USED % (H, H), instant=True)], w=6,
             unit="percent", decimals=1, thr=PCT_USED, graph="area",
             desc="Against MemAvailable, so page cache is counted as free — which it effectively is."),
        stat("Swap in use",
             [q("node_memory_SwapTotal_bytes{%s} - node_memory_SwapFree_bytes{%s}" % (H, H), instant=True)],
             w=6, unit="bytes", decimals=1,
             thr=thresholds(("green", None), ("yellow", 1), ("orange", 1073741824)),
             desc="Any swap in use on a host with RAM to spare is worth a look; sustained growth is a leak."),
        stat("Root filesystem", [q(inv.fs_used_pct(sel(H, 'mountpoint="/"')), instant=True)], w=6,
             unit="percent", decimals=1, thr=PCT_USED, graph="area"),
    ]
    if n["temp"]:
        tiles.append(stat("CPU package", [q("max(%s)" % (PKG_TEMP_F % H), instant=True)], w=6,
                          unit="fahrenheit", decimals=0, thr=TEMP_F, graph="area",
                          desc="At the die. Intel reports it as Package id 0, AMD as Tctl."))
    else:
        tiles.append(stat("Processes running", [q("node_procs_running{%s}" % H, instant=True)], w=6,
                          decimals=0, color_mode="none", graph="area",
                          desc="Processes in the run queue at the moment of the scrape."))
    g.extend(tiles)

    # ---------------------------------------------------------------- CPU
    g.section("CPU", "Where the time goes, and whether anything is waiting for it.")
    cpu_panels = [
        timeseries("CPU by mode",
                   [q("sum by (mode) (rate(node_cpu_seconds_total{%s, mode!=\"idle\"}[$__rate_interval]))"
                      " / on () group_left () count(count by (cpu) (node_cpu_seconds_total{%s})) * 100" % (H, H),
                      "{{mode}}")],
                   unit="percent", h=9, stack=True, maxv=100,
                   desc="Normalised to one core's worth, so the stack tops out at 100% however many cores "
                        "the host has. A tall iowait band is a disk problem wearing a CPU costume."),
        timeseries("Load average",
                   [q("node_load1{%s}" % H, "1 minute"),
                    q("node_load5{%s}" % H, "5 minutes", ref="B"),
                    q("node_load15{%s}" % H, "15 minutes", ref="C"),
                    q("count by (host) (count by (host, cpu) (node_cpu_seconds_total{%s}))" % H, "cores", ref="D")],
                   h=9, decimals=2,
                   desc="The flat line is the core count. Load above it means the run queue is longer than "
                        "the machine is wide.",
                   overrides=[by_name("cores", [("custom.lineStyle", {"fill": "dash", "dash": [8, 6]}),
                                                ("custom.lineWidth", 1), ("color", fixed("text"))])]),
    ]
    if n["psi"]:
        cpu_panels.append(timeseries(
            "CPU pressure",
            [q("rate(node_pressure_cpu_waiting_seconds_total{%s}[$__rate_interval]) * 100" % H, "some")],
            h=8, unit="percent", maxv=100, thr=thresholds(("green", None), ("yellow", 10), ("orange", 30)),
            desc="Share of time at least one task was runnable but waiting for a core. This is the honest "
                 "measure of CPU contention; utilisation is not."))
    if n["cpufreq"]:
        cpu_panels.append(timeseries(
            "Clock speed", [q("node_cpu_scaling_frequency_hertz{%s}" % H, "core {{cpu}}")],
            h=8, unit="hertz", legend=LEGEND_LIST, min_zero=False,
            desc="Cores parked at the floor under load mean thermal or power limiting."))
    for i, p in enumerate(cpu_panels):
        p["gridPos"]["w"] = 12
    g.extend(cpu_panels)

    # ------------------------------------------------------------- Memory
    g.section("Memory", "Where the RAM went. Cache is not a leak.")
    mem_overrides = [
        by_name("used", [("color", fixed("blue"))]),
        by_name("buffers", [("color", fixed("purple"))]),
        by_name("cached", [("color", fixed("super-light-blue"))]),
        by_name("free", [("color", fixed("text"))]),
    ]
    mem_panels = [
        timeseries("Memory breakdown",
                   [q("node_memory_MemTotal_bytes{%s} - node_memory_MemFree_bytes{%s}"
                      " - node_memory_Buffers_bytes{%s} - node_memory_Cached_bytes{%s}" % (H, H, H, H), "used"),
                    q("node_memory_Buffers_bytes{%s}" % H, "buffers", ref="B"),
                    q("node_memory_Cached_bytes{%s}" % H, "cached", ref="C"),
                    q("node_memory_MemFree_bytes{%s}" % H, "free", ref="D")],
                   w=12, h=9, unit="bytes", stack=True, overrides=mem_overrides,
                   desc="Stacked to total RAM. Only the blue band is memory a process actually holds."),
        timeseries("Swap",
                   [q("node_memory_SwapTotal_bytes{%s} - node_memory_SwapFree_bytes{%s}" % (H, H), "in use"),
                    q("node_memory_SwapTotal_bytes{%s}" % H, "configured", ref="B")],
                   w=12, h=9, unit="bytes",
                   overrides=[by_name("configured", [("custom.lineStyle", {"fill": "dash", "dash": [8, 6]}),
                                                     ("custom.lineWidth", 1), ("color", fixed("text"))])]),
    ]
    if n["psi"]:
        mem_panels.append(timeseries(
            "Memory pressure",
            [q("rate(node_pressure_memory_waiting_seconds_total{%s}[$__rate_interval]) * 100" % H, "some")],
            w=12, h=8, unit="percent", maxv=100,
            thr=thresholds(("green", None), ("yellow", 1), ("orange", 10)),
            desc="Time spent reclaiming rather than working. Non-zero here, before the OOM killer runs, is "
                 "the early warning."))
    mem_panels.append(timeseries(
        "Major page faults",
        [q("rate(node_vmstat_pgmajfault{%s}[$__rate_interval])" % H, "major faults/s")],
        w=12, h=8, unit="reqps",
        desc="Faults that had to go to disk. Sustained non-zero means the working set no longer fits."))
    g.extend(mem_panels)

    # -------------------------------------------------------- Filesystems
    g.section("Filesystems", "Real mounts only.")
    g.add(bargauge("Used", [q(inv.fs_used_pct(H), "{{mountpoint}}", instant=True)], w=12, h=9))
    g.add(joined_table(
        "Detail",
        [("A", inv.fs_used_pct(H), "Used",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge()),
         ("B", "node_filesystem_avail_bytes{%s}" % sel(FS, H), "Free", [("unit", "bytes"), ("decimals", 1)]),
         ("C", "node_filesystem_size_bytes{%s}" % sel(FS, H), "Size", [("unit", "bytes"), ("decimals", 1)]),
         ("D", "100 * (1 - node_filesystem_files_free{%s} / node_filesystem_files{%s})"
               % (sel(FS, H), sel(FS, H)), "Inodes",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge())],
        w=12, h=9, join_on="mountpoint", keep=r"^(mountpoint|device|fstype|Value #.*)$", sort=("Used", True),
        extra_overrides=[by_name("mountpoint", [("displayName", "Mount"), ("custom.width", 150)]),
                         by_name("device", [("displayName", "Device")]),
                         by_name("fstype", [("displayName", "Type"), ("custom.width", 80)])]))
    g.add(timeseries("Used over time", [q(inv.fs_used_pct(H), "{{mountpoint}}")],
                     w=24, h=8, unit="percent", maxv=100, thr=PCT_USED, thr_style="dashed"))

    # --------------------------------------------------------------- Disk
    disk_note = ("Physical devices as this host sees them. " +
                 ("Because an LXC guest shares the node's kernel, /proc/diskstats is not namespaced: "
                  "these are **%s**'s disks, and the traffic on them includes every other guest."
                  % n.get("pve", "the node")
                  if kind == "lxc" else
                  "These are this machine's own virtual disks." if kind == "qemu" else
                  "These are the physical drives in the machine."))
    g.section("Disk", disk_note)
    D = sel(DISK, H)
    disk_panels = [
        timeseries("Throughput",
                   [q("rate(node_disk_read_bytes_total{%s}[$__rate_interval])" % D, "{{device}} read"),
                    q("-1 * rate(node_disk_written_bytes_total{%s}[$__rate_interval])" % D,
                      "{{device}} write", ref="B")],
                   w=12, h=9, unit="Bps", min_zero=False,
                   desc="Reads above the line, writes below it."),
        timeseries("Operations",
                   [q("rate(node_disk_reads_completed_total{%s}[$__rate_interval])" % D, "{{device}} read"),
                    q("-1 * rate(node_disk_writes_completed_total{%s}[$__rate_interval])" % D,
                      "{{device}} write", ref="B")],
                   w=12, h=9, unit="iops", min_zero=False),
        timeseries("Utilisation",
                   [q("rate(node_disk_io_time_seconds_total{%s}[$__rate_interval]) * 100" % D, "{{device}}")],
                   w=12, h=8, unit="percent", maxv=100, thr=PCT_LOAD,
                   desc="Share of wall time with at least one request in flight. Sustained 100% is saturation."),
    ]
    if n["psi"]:
        disk_panels.append(timeseries(
            "I/O pressure",
            [q("rate(node_pressure_io_waiting_seconds_total{%s}[$__rate_interval]) * 100" % H, "some")],
            w=12, h=8, unit="percent", maxv=100,
            thr=thresholds(("green", None), ("yellow", 10), ("orange", 30)),
            desc="Time tasks spent blocked on storage."))
    else:
        disk_panels.append(timeseries(
            "Queue time",
            [q("rate(node_disk_io_time_weighted_seconds_total{%s}[$__rate_interval])" % D, "{{device}}")],
            w=12, h=8, unit="s",
            desc="Weighted I/O time: seconds of request-time accumulated per second. Above 1 means requests "
                 "are queueing."))
    g.extend(disk_panels)

    # ------------------------------------------------------------ Network
    g.section("Network", "Physical and bridge interfaces. Container veths and Proxmox firewall bridges are "
                         "filtered out.")
    N = sel(NET, H)
    net_panels = [
        timeseries("Throughput",
                   [q("rate(node_network_receive_bytes_total{%s}[$__rate_interval])" % N, "{{device}} in"),
                    q("-1 * rate(node_network_transmit_bytes_total{%s}[$__rate_interval])" % N,
                      "{{device}} out", ref="B")],
                   w=12, h=9, unit="Bps", min_zero=False,
                   desc="Inbound above the line, outbound below it."),
        timeseries("Errors and drops",
                   [q("rate(node_network_receive_errs_total{%s}[$__rate_interval])" % N, "{{device}} in errors"),
                    q("rate(node_network_transmit_errs_total{%s}[$__rate_interval])" % N, "{{device}} out errors", ref="B"),
                    q("rate(node_network_receive_drop_total{%s}[$__rate_interval])" % N, "{{device}} in drops", ref="C"),
                    q("rate(node_network_transmit_drop_total{%s}[$__rate_interval])" % N, "{{device}} out drops", ref="D")],
                   w=12, h=9, unit="pps", thr=thresholds(("green", None), ("orange", 1)),
                   desc="Flat zero is the healthy shape."),
        timeseries("TCP connections",
                   [q("node_netstat_Tcp_CurrEstab{%s}" % H, "established"),
                    q("node_sockstat_TCP_tw{%s}" % H, "time-wait", ref="B")],
                   w=12, h=8, decimals=0),
        timeseries("TCP retransmits",
                   [q("rate(node_netstat_Tcp_RetransSegs{%s}[$__rate_interval])" % H, "retransmitted"),
                    q("rate(node_netstat_Tcp_OutSegs{%s}[$__rate_interval])" % H, "sent", ref="B")],
                   w=12, h=8, unit="pps",
                   desc="Retransmits against total segments sent. The ratio is what matters, not the count."),
    ]
    if n["conntrack"]:
        net_panels.append(gauge(
            "Connection tracking table",
            [q("node_nf_conntrack_entries{%s} / node_nf_conntrack_entries_limit{%s} * 100" % (H, H), instant=True)],
            w=8, h=8,
            desc="Filling this table makes the host drop new connections without logging anything useful."))
        net_panels.append(timeseries(
            "Tracked connections",
            [q("node_nf_conntrack_entries{%s}" % H, "entries"),
             q("node_nf_conntrack_entries_limit{%s}" % H, "limit", ref="B")],
            w=16, h=8, decimals=0,
            overrides=[by_name("limit", [("custom.lineStyle", {"fill": "dash", "dash": [8, 6]}),
                                         ("custom.lineWidth", 1), ("color", fixed("text"))])]))
    else:
        net_panels.append(timeseries(
            "Sockets in use",
            [q("node_sockstat_TCP_inuse{%s}" % H, "TCP"),
             q("node_sockstat_UDP_inuse{%s}" % H, "UDP", ref="B")],
            w=24, h=8, decimals=0,
            desc="This host has no nf_conntrack module loaded, so there is no connection table to show."))
    g.extend(net_panels)

    # ----------------------------------------------------------- Hardware
    if n["temp"] or n["nvme"] or n["smart"] or n["zfs"]:
        g.section("Hardware", "Sensors and drives that belong to this physical machine.")
    if n["temp"]:
        g.add(timeseries(
            "Temperatures",
            [q("%s" % (PKG_TEMP_F % H), "package"),
             q("node_hwmon_temp_celsius{%s} * on (host, chip, sensor) group_left (label)"
               " node_hwmon_sensor_label{label=~\"Core .*|Tccd.*\"} * 9 / 5 + 32" % H, "{{label}}", ref="B")],
            w=24, h=9, unit="fahrenheit", thr=TEMP_F, thr_style="dashed", min_zero=False,
            desc="Package first, then each core. The four Intel nodes report per-core sensors as "
                 "`Core N`; grey-server is AMD and reports one per-die sensor, `Tccd1`, so both are matched. "
                 "node_hwmon reports Celsius, so the query converts and the thresholds move with it — "
                 "changing only the display unit would label a Celsius number as Fahrenheit."))
    if n["nvme"]:
        g.add(joined_table(
            "NVMe",
            [("A", "nvme_critical_warning{%s}" % H, "Warning",
              [CELL_COLOR_BG, ("thresholds", BAD_ABOVE_ZERO), ("decimals", 0), ("custom.width", 100)]),
             ("B", "nvme_temperature_celsius{%s} * 9 / 5 + 32" % H, "Temp",
              [("unit", "fahrenheit"), ("decimals", 0), ("thresholds", TEMP_F), CELL_COLOR_TEXT]),
             ("C", "nvme_available_spare_ratio{%s} * 100" % H, "Spare",
              [("unit", "percent"), ("decimals", 0),
               ("thresholds", thresholds(("red", None), ("orange", 10), ("green", 30)))] + cell_gauge()),
             ("D", "nvme_percentage_used_ratio{%s} * 100" % H, "Endurance used",
              [("unit", "percent"), ("decimals", 0), ("thresholds", PCT_USED)] + cell_gauge()),
             ("E", "nvme_power_on_hours_total{%s}" % H, "Powered on", [("unit", "h"), ("decimals", 0)]),
             ("F", "nvme_media_errors_total{%s}" % H, "Media errors",
              [("decimals", 0), CELL_COLOR_TEXT, ("thresholds", BAD_ABOVE_ZERO)]),
             ("G", "nvme_unsafe_shutdowns_total{%s}" % H, "Unsafe stops", [("decimals", 0)])],
            w=12, h=7, join_on="device", keep=r"^(device|Value #.*)$",
            extra_overrides=[by_name("device", [("displayName", "Device"), ("custom.width", 110)])]))
        g.add(timeseries("NVMe temperature",
                         [q("nvme_temperature_celsius{%s} * 9 / 5 + 32" % H, "{{device}}")],
                         w=12, h=7, unit="fahrenheit", thr=TEMP_F, thr_style="dashed", min_zero=False))
    if n["smart"]:
        g.add(joined_table(
            "SMART",
            [("A", "smartmon_device_smart_healthy{%s}" % H, "Assessment",
              [CELL_COLOR_BG, ("mappings", mapping({0: ("not reported", "text"), 1: ("PASSED", "green")})),
               ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 120)]),
             ("B", "(smartmon_temperature_celsius_raw_value{%s}"
               " or smartmon_airflow_temperature_cel_raw_value{%s}) * 9 / 5 + 32" % (H, H), "Temp",
              [("unit", "fahrenheit"), ("decimals", 0), ("thresholds", TEMP_F), CELL_COLOR_TEXT]),
             ("C", "smartmon_power_on_hours_raw_value{%s}" % H, "Powered on", [("unit", "h"), ("decimals", 0)]),
             ("D", "smartmon_reallocated_sector_ct_raw_value{%s}" % H, "Reallocated",
              [("decimals", 0), CELL_COLOR_TEXT, ("thresholds", BAD_ABOVE_ZERO)]),
             ("E", "smartmon_power_cycle_count_raw_value{%s}" % H, "Power cycles", [("decimals", 0)])],
            w=24, h=6, join_on="disk", keep=r"^(disk|Value #.*)$",
            desc="Only the attributes every drive here reports. Pending sectors and UDMA CRC errors are "
                 "ATA attributes the Samsung SSD in purple-server does not expose, so they live on "
                 "[Storage & Drive Health](/d/storage-health) instead. The NVMe controller reports no "
                 "overall self-assessment, so its row reads `not reported`; its health is in the NVMe "
                 "table above.",
            extra_overrides=[by_name("disk", [("displayName", "Disk"), ("custom.width", 140)])]))
    if n["zfs"]:
        g.add(stat("ZFS pool state",
                   [q('max by (zpool) (node_zfs_zpool_state{state="online", %s})' % H, "{{zpool}}", instant=True)],
                   w=8, h=7, mappings=mapping({0: ("NOT ONLINE", "red"), 1: ("ONLINE", "green")}),
                   thr=GOOD_ABOVE_ZERO, color_mode="background", text_mode="value_and_name"))
        g.add(timeseries("ZFS ARC size", [q("node_zfs_arc_size{%s}" % H, "ARC")],
                         w=8, h=7, unit="bytes"))
        g.add(timeseries("ZFS ARC hit ratio",
                         [q("100 * rate(node_zfs_arc_hits{%s}[$__rate_interval]) / clamp_min("
                            "rate(node_zfs_arc_hits{%s}[$__rate_interval])"
                            " + rate(node_zfs_arc_misses{%s}[$__rate_interval]), 1)" % (H, H, H), "hit ratio")],
                         w=8, h=7, unit="percent", maxv=100,
                         thr=thresholds(("red", None), ("orange", 80), ("green", 95))))

    # ------------------------------------------------------------- Guests
    if kind == "metal":
        g.section("Guests on this node", "What this node is actually carrying.")
        g.add(empty_ok(joined_table(
            "Guests on %s" % host,
            [("A", 'pve_up{%s} * on (id) group_left (name, node, type) pve_guest_info{node="%s"}' % (GUEST, host), "Up",
              [CELL_COLOR_BG, ("mappings", MAP_UP_DOWN), ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 70)]),
             ("B", "pve_cpu_usage_ratio{%s} * 100" % GUEST, "CPU",
              [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_LOAD)] + cell_gauge()),
             ("C", "pve_memory_usage_bytes{%s} / pve_memory_size_bytes{%s} * 100" % (GUEST, GUEST), "Memory",
              [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge()),
             ("D", "pve_memory_size_bytes{%s}" % GUEST, "RAM", [("unit", "bytes"), ("decimals", 0)]),
             ("E", "pve_disk_size_bytes{%s}" % GUEST, "Disk", [("unit", "bytes"), ("decimals", 0)]),
             ("F", "pve_uptime_seconds{%s}" % GUEST, "Uptime", [("unit", "s"), ("decimals", 0)])],
            w=24, h=9, join_on="id", keep=r"^(id|name|type|Value #.*)$", sort=("CPU", True),
            desc="Joined against pve_guest_info filtered to this node, so only this node's guests appear.",
            extra_overrides=[
                by_name("id", [("displayName", "ID"), ("custom.width", 90)]),
                by_name("name", [("displayName", "Guest"), ("custom.width", 180),
                                 ("links", [{"title": "Open this host's dashboard",
                                             "url": "/d/node-${__value.raw}", "targetBlank": False}])]),
                by_name("type", [("displayName", "Type"), ("custom.width", 80)])],
            no_value="No guest is registered on this node.")))
        g.add(empty_ok(timeseries(
            "Guest CPU on %s" % host,
            [q('topk(8, pve_cpu_usage_ratio{%s} * 100 * on (id) group_left () '
               'pve_guest_info{node="%s"})' % (GUEST, host), "{{id}}")],
            w=24, h=8, unit="percent", thr=PCT_LOAD,
            desc="Top eight guests on this node.")))

    # --------------------------------------------------------- Containers
    if n["docker"]:
        ct = sel(CT, H)
        g.section("Containers on this host", "From cAdvisor, which sees the container boundary the host "
                                             "itself does not.")
        g.add(joined_table(
            "Containers",
            [("A", "sum by (name, image) (rate(container_cpu_usage_seconds_total{%s}[$__rate_interval])) * 100" % ct,
              "CPU", [("unit", "percent"), ("decimals", 2), ("thresholds", PCT_LOAD)] + cell_gauge(0, 200)),
             ("B", "sum by (name) (container_memory_working_set_bytes{%s})" % ct, "Memory",
              [("unit", "bytes"), ("decimals", 1)]),
             ("C", "max by (name) (time() - container_start_time_seconds{%s})" % ct, "Up for",
              [("unit", "s"), ("decimals", 0), CELL_COLOR_TEXT,
               ("thresholds", thresholds(("orange", None), ("green", 3600)))]),
             ("D", "sum by (name) (rate(container_network_receive_bytes_total{%s}[$__rate_interval]))" % ct,
              "Net in", [("unit", "Bps"), ("decimals", 1)]),
             ("E", "sum by (name) (rate(container_network_transmit_bytes_total{%s}[$__rate_interval]))" % ct,
              "Net out", [("unit", "Bps"), ("decimals", 1)])],
            w=24, h=10, join_on="name", keep=r"^(name|image|Value #.*)$", sort=("CPU", True),
            desc="`Up for` turns amber under an hour, which is how a restart loop announces itself.",
            extra_overrides=[by_name("name", [("displayName", "Container"), ("custom.width", 220)]),
                             by_name("image", [("displayName", "Image")])]))
        g.add(timeseries(
            "Container CPU",
            [q("topk(10, sum by (name) (rate(container_cpu_usage_seconds_total{%s}[$__rate_interval])) * 100)" % ct,
               "{{name}}")], w=12, h=9, unit="percent"))
        g.add(timeseries(
            "Container memory",
            [q("topk(10, sum by (name) (container_memory_working_set_bytes{%s}))" % ct, "{{name}}")],
            w=12, h=9, unit="bytes"))

    # ---------------------------------------------------------------- UPS
    if n.get("ups"):
        u = n["ups"]
        g.section("Power", "This node is read by the NUT server for %s. Full detail on "
                           "[Power & UPS](/d/power-ups)." % u)
        g.extend([
            stat("Mains", [q('nut_ups_status{status="OL", ups="%s"}' % u, instant=True)], w=6, h=5,
                 mappings=mapping({0: ("ON BATTERY", "red"), 1: ("ON MAINS", "green")}),
                 thr=GOOD_ABOVE_ZERO, color_mode="background", text_mode="value"),
            stat("Battery", [q('nut_battery_charge{ups="%s"} * 100' % u, instant=True)], w=6, h=5,
                 unit="percent", decimals=0, maxv=100,
                 thr=thresholds(("red", None), ("orange", 30), ("yellow", 60), ("green", 90))),
            stat("Runtime left", [q('nut_battery_runtime_seconds{ups="%s"}' % u, instant=True)], w=6, h=5,
                 unit="s", decimals=0,
                 thr=thresholds(("red", None), ("orange", 300), ("yellow", 900), ("green", 1800))),
            stat("Load", [q('nut_load{ups="%s"} * 100' % u, instant=True)], w=6, h=5,
                 unit="percent", decimals=0, maxv=100, thr=PCT_LOAD),
        ])

    # -------------------------------------------------------------- Facts
    g.section("Facts", "What this machine is, and the housekeeping nobody looks at until it matters.")
    g.extend([
        stat("Booted", [q("node_boot_time_seconds{%s} * 1000" % H, instant=True)], w=6, h=5,
             unit="dateTimeAsLocal", color_mode="none", text_mode="value"),
        stat("Cores", [q("count by (host) (count by (host, cpu) (node_cpu_seconds_total{%s}))" % H, instant=True)],
             w=6, h=5, decimals=0, color_mode="none"),
        stat("Total RAM", [q("node_memory_MemTotal_bytes{%s}" % H, instant=True)], w=6, h=5,
             unit="bytes", decimals=1, color_mode="none"),
        stat("Clock offset", [q("node_timex_offset_seconds{%s}" % H, instant=True)], w=6, h=5,
             unit="s", decimals=6,
             thr=thresholds(("green", None), ("yellow", 0.05), ("orange", 0.5)),
             desc="Against the NTP source. A drifting clock quietly ruins every graph on this page."),
    ])
    g.add(table(
        "Identity",
        [tq("node_uname_info{%s}" % H), tq("node_os_info{%s}" % H, ref="B"),
         tq("node_exporter_build_info{%s}" % H, ref="C")],
        w=24, h=4,
        transformations=[
            {"id": "joinByField", "options": {"byField": "host", "mode": "outer"}},
            {"id": "filterFieldsByName",
             "options": {"include": {"pattern": r"^(nodename|pretty_name|release|machine|version)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                {"nodename": "Hostname", "pretty_name": "Operating system", "release": "Kernel",
                 "machine": "Architecture", "version": "node_exporter"},
             "indexByName": {"nodename": 0, "pretty_name": 1, "release": 2, "machine": 3, "version": 4}}}]))
    if n["systemd"]:
        g.add(empty_ok(table(
            "Failed units on %s" % host,
            [tq('node_systemd_unit_state{state="failed", %s} == 1' % H)],
            w=12, h=7, no_value="No unit is in the failed state.",
            transformations=[
                {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(name)$"}}},
                {"id": "organize", "options": {"excludeByName": {}, "renameByName": {"name": "Unit"},
                                               "indexByName": {"name": 0}}}])))
    if n["apt"]:
        g.add(empty_ok(table(
            "Pending updates on %s" % host,
            [tq("apt_upgrades_pending{%s} > 0" % H)],
            w=12, h=7, no_value="No pending updates.",
            transformations=[
                {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(origin|arch|Value)$"}}},
                {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                    {"origin": "Origin", "arch": "Architecture", "Value": "Packages"},
                 "indexByName": {"origin": 0, "arch": 1, "Value": 2}}}],
            overrides=[by_name("Packages", [("decimals", 0), CELL_COLOR_TEXT,
                                            ("thresholds", thresholds(("yellow", None), ("orange", 20)))])])))

    return dashboard(
        "node-%s" % host, host, g,
        tags=["node", n["role"], kind],
        description="%s — %s at %s." % (host, inv.WHAT_IS_IT[kind], n["ip"]),
        refresh="30s", time_from="now-6h")


# ======================================================================= main

def main() -> int:
    OUT_TOPIC.mkdir(parents=True, exist_ok=True)
    OUT_NODES.mkdir(parents=True, exist_ok=True)

    topic = [overview(), proxmox(), containers(), services(), storage(),
             network(), power(), monitoring(), teamspeak()]

    written = 0
    for d in topic:
        (OUT_TOPIC / ("%s.json" % d["uid"])).write_text(
            json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written += 1
    for n in inv.NODES:
        d = node_dashboard(n)
        (OUT_NODES / ("%s.json" % d["uid"])).write_text(
            json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written += 1

    (ROOT / "Tests/allow-empty.json").write_text(
        json.dumps(sorted(ALLOW_EMPTY), indent=2) + "\n", encoding="utf-8")

    def count(d):
        total = 0
        for p in d["panels"]:
            if p["type"] == "row":
                total += sum(1 for c in p.get("panels", []) if c["type"] != "text")
            elif p["type"] != "text":
                total += 1
        return total

    print("%d dashboards" % written)
    for d in topic:
        print("  %-28s %-34s %3d panels" % (d["uid"], d["title"], count(d)))
    print("  %-28s %-34s %3d panels (18 files)"
          % ("node-*", "one per host", count(node_dashboard(inv.NODES[0]))))
    print("%d panel titles registered as allowed-empty" % len(ALLOW_EMPTY))
    return 0


if __name__ == "__main__":
    sys.exit(main())
