#!/usr/bin/env python3
"""Generate every Homelab Grafana dashboard from one description.

Run it, commit what it writes, deploy the directory. Nothing else edits the
dashboard JSON.

    python3 Tools/build_dashboards.py

Output:
    Configuration/grafana/dashboards/homelab/*.json   -> Grafana folder "Homelab"
    Configuration/grafana/dashboards/nodes/*.json     -> Grafana folder "Nodes"
    Tests/allow-empty.json                            -> read by the query assertion

Why generated. There is one dashboard per host, and seventeen hand-maintained
copies of the same layout diverge the first time one of them is edited. The
per-node layout lives in `node_dashboard()` once, and each host's capability
flags in `inventory.py` decide which sections it grows.

Panel form follows the data's job rather than habit:

    a single current value            stat tile: one large centred number
    a ratio against a known limit     bar gauge, one bar per thing
    change over time, <= 8 series     time series
    change over time, many series     time series of the top N, plus a table that
                                      covers all of them
    up or down over time              state timeline
    one row per thing, many columns   table, with the magnitude column drawn as
                                      an in-cell bar
    a list that should normally be
    empty                             table, with the empty state spelled out

A panel carries its number and nothing else: no bands of prose under a row
header, no sparkline inside a tile, no legend table under a graph, and a
description only where the value is computed in a way the title cannot say.

Colour is either state or resource. Tiles, cells and bars are coloured by their
thresholds. A single-series graph wears its resource's tint from dashlib.TINT,
so CPU is the same salmon on every dashboard; a graph of several series colours
by series name, so a host keeps its colour when a filter changes the count.
"""
from __future__ import annotations

import json
import pathlib
import sys

import uptime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from dashlib import (CELL_COLOR_BG, CELL_COLOR_TEXT, CERT_DAYS, GOOD_ABOVE_ZERO,
                     BAD_ABOVE_ZERO, Grid, LEGEND_LIST, LEGEND_OFF, LOAD_PER_CORE,
                     MAP_OK_FAIL, MAP_UP_DOWN, PCT_LOAD, PCT_USED, TEMP_F,
                     bargauge, by_name, by_regex, cell_gauge, dashboard, fixed,
                     gauge, mapping, out_of, q, stat, state_timeline, table,
                     thresholds, timeseries, tq, var_query)
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
                 join_on="host", keep=r"^(host|role|Value #.*)$", no_value="no data",
                 exclude=None, index=None):
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
    if index:
        order.update(index)
    return table(
        title, targets, w=w, h=h, desc=desc, sort=sort, no_value=no_value,
        transformations=[
            {"id": "joinByField", "options": {"byField": join_on, "mode": "outer"}},
            {"id": "filterFieldsByName", "options": {"include": {"pattern": keep}}},
            {"id": "organize", "options": {"excludeByName": {k: True for k in (exclude or [])},
                                           "renameByName": rename, "indexByName": order}},
        ],
        overrides=overrides + (extra_overrides or []),
    )


# node_exporter collectors that succeed on no host in this fleet: there is no
# fibre channel, InfiniBand, IPVS, NFS or tape anywhere, so counting them as
# "inactive" is noise. What is left is a per-host kernel-feature count, which
# sits between two and six, so the step is set above that rather than at one.
NO_COLLECTOR = "fibrechannel|infiniband|ipvs|nfs|nfsd|tapestats"

# Denominators. Derive what the inventory knows; a hand-typed total goes stale
# silently and the tile then sits amber where nobody questions it.
HYPERVISORS = len(inv.HYPERVISORS)
DOCKER_HOSTS = sum(1 for n in inv.NODES if n["docker"])
ZFS_HOST = next(n["host"] for n in inv.NODES if n["zfs"])
# The names published through Nginx Proxy Manager. Not in the inventory, which
# describes hosts; check it against `count(probe_success{instance=~"https://.*"})`.
PUBLISHED_SERVICES = len(uptime.HTTP_SERVICES)

# cAdvisor reports one series per interface in the container's netns, so a
# network_mode: host container reports every bridge on the box and its traffic
# adds up to several times the host NIC's.
CT_IFACE = 'interface!~"br-.*|docker.*|lo|veth.*"'
CT_KEY = '%s by (ct) (label_join(%s, "ct", "@", "name", "host"))'
FS_KEY_A = 'label_join(%s, "fs", "@", "host", "mountpoint")'
FS_KEY = 'max by (fs) (label_join(%s, "fs", "@", "host", "mountpoint"))'
SMART_OK = ' and on (host, disk) smartmon_device_smart_available == 1'
DK_KEY_A = 'label_join(%s, "dk", "@", "host", "disk")'
DK_KEY = 'max by (dk) (label_join(%s' + SMART_OK + ', "dk", "@", "host", "disk"))'


def all_of(n):
    """Thresholds for a count that is only healthy at its full total."""
    return thresholds(("red", None), ("orange", n - 1), ("green", n))


HOST_LINK = ("links", [{"title": "Open this node's dashboard",
                        "url": "/d/node-${__value.raw}", "targetBlank": False}])


# ============================================================ Homelab Overview

def overview():
    g = Grid()

    g.section("Right now")
    g.extend([
        stat("Cluster quorum", [q('pve_up{id="cluster/Galaxy"}', instant=True)], w=6,
             mappings=mapping({0: ("NOT QUORATE", "red"), 1: ("QUORATE", "green")}),
             thr=GOOD_ABOVE_ZERO, text_mode="value"),
        stat("Proxmox nodes online", [q('sum(pve_up{id=~"node/.*"})', instant=True)], w=6,
             unit=out_of(HYPERVISORS), thr=all_of(HYPERVISORS), maxv=HYPERVISORS),
        stat("Guests running", [q('sum(pve_up{id=~"(qemu|lxc)/.*"})', instant=True)], w=6),
        stat("Services reachable", [q('sum(probe_success{instance=~"https://.*"})', instant=True)], w=6,
             unit=out_of(PUBLISHED_SERVICES), thr=all_of(PUBLISHED_SERVICES), maxv=PUBLISHED_SERVICES,
             desc="The published names, excluding the alert bot's internal health probe."),
        stat("Scrape targets down", [q("count(up == 0) or vector(0)", instant=True)], w=6,
             thr=BAD_ABOVE_ZERO),
        stat("UPS on mains", [q('min(nut_ups_status{status="OL"})', instant=True)], w=6,
             mappings=mapping({0: ("ON BATTERY", "red"), 1: ("ON MAINS", "green")}),
             thr=GOOD_ABOVE_ZERO, text_mode="value"),
        stat("Hottest CPU package", [q("max(%s)" % (PKG_TEMP_F % 'role="hypervisor"'), instant=True)],
             w=6, unit="fahrenheit", decimals=0, thr=TEMP_F),
        stat("Fullest filesystem", [q("max(%s)" % inv.fs_used_pct(), instant=True)], w=6,
             unit="percent", decimals=1, thr=PCT_USED),
    ])

    g.section("Needs attention")
    g.add(empty_ok(table(
        "Anything failing a health check",
        [tq(NEEDS_ATTENTION)],
        h=8,
        no_value="All clear",
        transformations=[
            {"id": "filterFieldsByName",
             "options": {"include": {"pattern": r"^(check|object|host|Value)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                {"check": "Check", "object": "Object", "host": "Host", "Value": "Reading"},
             "indexByName": {"check": 0, "object": 1, "host": 2, "Value": 3}}},
        ],
        overrides=[by_name("Check", [CELL_COLOR_BG, ("thresholds", thresholds(("red", None)))])],
        sort=("Check", False))))

    g.section("Nodes")
    g.add(joined_table(
        "Fleet",
        [("A", 'max by (host, role) (up{job="node"})', "Up",
          [CELL_COLOR_BG, ("mappings", MAP_UP_DOWN), ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 70)]),
         ("B", "max by (host) (time() - node_boot_time_seconds)", "Uptime",
          [("unit", "s"), ("decimals", 0), ("custom.width", 120)]),
         ("C", inv.CORES % "", "Cores",
          [("custom.width", 70)]),
         ("D", inv.CPU_BUSY % ("", ""), "CPU",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_LOAD)] + cell_gauge()),
         ("E", "max by (host) (node_load1) / on (host) group_left () " + (inv.CORES % ""), "Load / core",
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
        extra_overrides=[by_name("host", [HOST_LINK, ("custom.width", 150),
                                          ("displayName", "Host")]),
                         by_name("role", [("custom.width", 110), ("displayName", "Role")])]))
    g.extend([
        timeseries("CPU · top 5",
                   [q("topk(5, %s)" % (inv.CPU_BUSY % ("", "")), "{{host}}")],
                   unit="percent", maxv=100, h=8, thr=PCT_LOAD),
        timeseries("Memory · top 5",
                   [q("topk(5, %s)" % (inv.MEM_USED % ("", "")), "{{host}}")],
                   unit="percent", maxv=100, h=8, thr=PCT_USED),
    ])

    g.section("Services")
    g.add(state_timeline(
        "Reachability", [q("probe_success", "{{instance}}")], h=10,
        mappings=mapping({0: ("down", "red"), 1: ("up", "green")}),
        legend=LEGEND_OFF))

    return dashboard(
        "homelab-overview", "Homelab Overview", g,
        tags=["homelab", "overview"],
        description="Fleet health, the node table and service reachability.",
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

    g.section("Cluster")
    g.extend([
        stat("Quorum", [q('pve_up{id="cluster/Galaxy"}', instant=True)], w=8,
             mappings=mapping({0: ("NOT QUORATE", "red"), 1: ("QUORATE", "green")}),
             thr=GOOD_ABOVE_ZERO, text_mode="value"),
        stat("Nodes online", [q("sum(pve_up{%s})" % NODE_ID, instant=True)], w=8,
             unit=out_of(HYPERVISORS), thr=all_of(HYPERVISORS), maxv=HYPERVISORS),
        stat("Guests running", [q("sum(pve_up{%s})" % GUEST, instant=True)], w=8),
        stat("Guests stopped", [q("count(pve_up{%s} == 0) or vector(0)" % GUEST, instant=True)], w=8,
             thr=thresholds(("green", None), ("yellow", 1)),
             desc="Templates and spare guests are stopped on purpose."),
        stat("Templates", [q('sum(pve_guest_info{template="1"})', instant=True)], w=8),
        stat("Guests with no backup", [q("sum(pve_not_backed_up_total) or vector(0)", instant=True)], w=8,
             thr=thresholds(("green", None), ("orange", 1)),
             desc="No vzdump archive on any storage Proxmox can see. This lab keeps no backups, "
                  "so it counts every guest."),
    ])

    g.section("Nodes")
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

    g.section("Guests")
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
        timeseries("Guest CPU · top 8",
                   [q("topk(8, pve_cpu_usage_ratio{%s} * 100)" % GUEST, "{{id}}")],
                   unit="percent", h=8, thr=PCT_LOAD),
        timeseries("Guest memory · top 8",
                   [q("topk(8, pve_memory_usage_bytes{%s} / pve_memory_size_bytes{%s} * 100)" % (GUEST, GUEST),
                      "{{id}}")],
                   unit="percent", maxv=100, h=8, thr=PCT_USED),
    ])

    g.section("Guest I/O")
    g.extend([
        timeseries("Disk read · top 8",
                   [q("topk(8, rate(pve_disk_read_bytes_total{%s}[$__rate_interval]))" % GUEST, "{{id}}")],
                   unit="Bps", h=8),
        timeseries("Disk write · top 8",
                   [q("topk(8, rate(pve_disk_written_bytes_total{%s}[$__rate_interval]))" % GUEST, "{{id}}")],
                   unit="Bps", h=8),
        timeseries("Network in · top 8",
                   [q("topk(8, rate(pve_network_receive_bytes_total{%s}[$__rate_interval]))" % GUEST, "{{id}}")],
                   unit="Bps", h=8),
        timeseries("Network out · top 8",
                   [q("topk(8, rate(pve_network_transmit_bytes_total{%s}[$__rate_interval]))" % GUEST, "{{id}}")],
                   unit="Bps", h=8),
    ])

    g.section("Storage")
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

    g.section("Fleet")
    g.extend([
        stat("Containers running", [q("count(container_last_seen{%s})" % ct, instant=True)], w=8),
        stat("Docker hosts reporting", [q("count(count by (host) (container_last_seen{%s}))" % CT, instant=True)],
             w=8, unit=out_of(DOCKER_HOSTS), thr=all_of(DOCKER_HOSTS), maxv=DOCKER_HOSTS),
        stat("Started in the last hour",
             [q("count(time() - container_start_time_seconds{%s} < 3600) or vector(0)" % ct, instant=True)],
             w=8, thr=thresholds(("green", None), ("yellow", 1), ("orange", 3))),
        stat("OOM kills, last 24h",
             [q("sum(increase(container_oom_events_total{%s}[24h])) or vector(0)" % ct, instant=True)],
             w=8, thr=BAD_ABOVE_ZERO),
        stat("Being CPU throttled",
             [q("count(rate(container_cpu_cfs_throttled_seconds_total{%s}[$__rate_interval]) > 0) or vector(0)" % ct,
                instant=True)],
             w=8, thr=thresholds(("green", None), ("yellow", 1))),
        stat("Memory in containers",
             [q("sum(container_memory_working_set_bytes{%s})" % ct, instant=True)],
             w=8, unit="bytes", decimals=1),
    ])

    g.section("Restarts and faults")
    g.add(empty_ok(table(
        "Started in the last 6 hours",
        [tq("time() - container_start_time_seconds{%s} < 21600" % ct)],
        w=12, h=8, unit="s", no_value="Nothing started in 6 hours",
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
        w=12, h=8, no_value="No OOM kills in 24 hours",
        transformations=[
            {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(host|name|Value)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                {"host": "Host", "name": "Container", "Value": "Kills"}, "indexByName": {"name": 0, "host": 1, "Value": 2}}}],
        sort=("Kills", True),
        overrides=[by_name("Kills", [CELL_COLOR_BG, ("thresholds", BAD_ABOVE_ZERO), ("decimals", 0)])])))

    g.section("CPU")
    g.extend([
        timeseries("CPU · top 10",
                   [q("topk(10, sum by (host, name) (rate(container_cpu_usage_seconds_total{%s}[$__rate_interval])) * 100)" % ct,
                      "{{name}} · {{host}}")],
                   unit="percent", h=9, desc="100% is one full core."),
        timeseries("CPU throttling · top 10",
                   [q("topk(10, sum by (host, name) (rate(container_cpu_cfs_throttled_seconds_total{%s}[$__rate_interval])) * 100)" % ct,
                      "{{name}} · {{host}}")],
                   unit="percent", h=9, thr=thresholds(("green", None), ("orange", 1))),
    ])

    g.section("Memory")
    g.extend([
        timeseries("Memory · top 10",
                   [q("topk(10, sum by (host, name) (container_memory_working_set_bytes{%s}))" % ct,
                      "{{name}} · {{host}}")],
                   unit="bytes", h=9),
        timeseries("Memory by host",
                   [q("sum by (host) (container_memory_working_set_bytes{%s})" % ct, "{{host}}")],
                   unit="bytes", h=9, stack=True),
    ])

    g.section("Every container")
    g.add(joined_table(
        "Containers",
        [("A", 'label_join(sum by (host, name, image) '
               '(rate(container_cpu_usage_seconds_total{%s}[$__rate_interval])) * 100, '
               '"ct", "@", "name", "host")' % ct,
          "CPU", [("unit", "percent"), ("decimals", 2), ("thresholds", PCT_LOAD)] + cell_gauge(0, 200)),
         ("B", CT_KEY % ("sum", "container_memory_working_set_bytes{%s}" % ct), "Memory",
          [("unit", "bytes"), ("decimals", 1)]),
         ("C", CT_KEY % ("sum", "container_spec_memory_limit_bytes{%s} > 0" % ct), "Limit",
          [("unit", "bytes"), ("decimals", 1), ("noValue", "none")]),
         ("D", CT_KEY % ("max", "time() - container_start_time_seconds{%s}" % ct), "Up for",
          [("unit", "s"), ("decimals", 0)]),
         ("E", CT_KEY % ("sum", "rate(container_network_receive_bytes_total{%s}[$__rate_interval])"
                                % sel(ct, CT_IFACE)), "Net in",
          [("unit", "Bps"), ("decimals", 1)]),
         ("F", CT_KEY % ("sum", "rate(container_network_transmit_bytes_total{%s}[$__rate_interval])"
                                % sel(ct, CT_IFACE)), "Net out",
          [("unit", "Bps"), ("decimals", 1)])],
        h=16, join_on="ct", keep=r"^(name|host|image|Value #.*)$", sort=("CPU", True),
        extra_overrides=[
            by_name("name", [("displayName", "Container"), ("custom.width", 220)]),
            by_name("host", [("displayName", "Host"), ("custom.width", 140), HOST_LINK]),
            by_name("image", [("displayName", "Image")])]))

    g.section("Network and disk")
    g.extend([
        timeseries("Network in · top 10",
                   [q("topk(10, sum by (host, name) (rate(container_network_receive_bytes_total{%s}[$__rate_interval])))" % ct,
                      "{{name}} · {{host}}")], unit="Bps", h=9),
        timeseries("Network out · top 10",
                   [q("topk(10, sum by (host, name) (rate(container_network_transmit_bytes_total{%s}[$__rate_interval])))" % ct,
                      "{{name}} · {{host}}")], unit="Bps", h=9),
        timeseries("Writable layer · top 10",
                   [q("topk(10, sum by (host, name) (container_fs_usage_bytes{%s}))" % ct, "{{name}} · {{host}}")],
                   unit="bytes", h=9, w=24),
    ])

    return dashboard(
        "containers", "Containers", g,
        tags=["homelab", "containers"],
        description="Every Docker workload across the %d cAdvisor hosts." % DOCKER_HOSTS,
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
            ' "https?://([^.:/]+).*")')


def services():
    g = Grid()
    svc = 'instance=~"$service"'

    g.section("Right now")
    g.extend([
        stat("Reachable", [q('sum(probe_success{instance=~"https://.*"})', instant=True)], w=8,
             unit=out_of(PUBLISHED_SERVICES), thr=all_of(PUBLISHED_SERVICES), maxv=PUBLISHED_SERVICES,
             desc="The published names, excluding the alert bot's internal health probe."),
        stat("Failing", [q("count(probe_success == 0) or vector(0)", instant=True)], w=8,
             thr=BAD_ABOVE_ZERO),
        stat("Slowest probe", [q("max(probe_duration_seconds)", instant=True)], w=8,
             unit="s", decimals=2, thr=thresholds(("green", None), ("yellow", 1), ("orange", 3), ("red", 8))),
        stat("Median probe", [q("quantile(0.5, probe_duration_seconds)", instant=True)], w=8,
             unit="s", decimals=3),
        stat("Nearest certificate expiry",
             [q("min((probe_ssl_earliest_cert_expiry - time()) / 86400)", instant=True)], w=8,
             unit="d", decimals=0, thr=CERT_DAYS),
        stat("24-hour availability", [q("avg(avg_over_time(probe_success[24h])) * 100", instant=True)], w=8,
             unit="percent", decimals=3,
             thr=thresholds(("red", None), ("orange", 99), ("yellow", 99.5), ("green", 99.9)),
             desc="The last 24 hours, whatever the time picker says."),
    ])

    g.section("Availability")
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
        extra_overrides=[by_name("service", [("displayName", "Service"), ("custom.width", 180)])]))

    g.section("Latency")
    g.extend([
        timeseries("Probe duration · top 8",
                   [q("topk(8, %s)" % (SVC_NAME % "probe_duration_seconds"), "{{service}}")],
                   unit="s", h=9),
        timeseries("Phase breakdown",
                   [q('sum by (phase) (probe_http_duration_seconds{%s})' % svc, "{{phase}}")],
                   unit="s", h=9, stack=True),
    ])

    g.section("TLS")
    g.add(bargauge(
        "Certificate days left",
        [q(SVC_NAME % "(probe_ssl_earliest_cert_expiry - time()) / 86400", "{{service}}", instant=True)],
        w=12, h=11, unit="d", decimals=0, maxv=90, thr=CERT_DAYS))
    g.add(timeseries(
        "Certificate lifetime",
        [q(SVC_NAME % "(probe_ssl_earliest_cert_expiry - time()) / 86400", "{{service}}")],
        w=12, h=11, unit="d", thr=CERT_DAYS, thr_style="dashed"))

    return dashboard(
        "services-uptime", "Services & Uptime", g,
        tags=["homelab", "services"],
        description="Twenty-three internal service names, probed end to end through the proxy.",
        refresh="1m", time_from="now-24h",
        templating=[var_query("service", "Service", "label_values(probe_success, instance)")])


# ===================================================== Storage & drive health

def storage():
    g = Grid()
    HV = 'role="hypervisor"'

    g.section("Headroom")
    g.extend([
        stat("Fullest filesystem", [q("max(%s)" % inv.fs_used_pct(), instant=True)], w=8,
             unit="percent", decimals=1, thr=PCT_USED),
        stat("Filesystems over 80%",
             [q("count(%s > 80) or vector(0)" % inv.fs_used_pct(), instant=True)], w=8,
             thr=thresholds(("green", None), ("yellow", 1), ("orange", 3))),
        stat("ZFS pools online",
             [q('sum(max by (host, zpool) (node_zfs_zpool_state{state="online",host="%s"}))' % ZFS_HOST,
                instant=True)],
             w=8, unit=out_of(1), thr=thresholds(("red", None), ("green", 1)), maxv=1,
             desc="node_zfs_zpool_state emits one series per pool state, not per dataset."),
        stat("NVMe critical warnings", [q("sum(nvme_critical_warning) or vector(0)", instant=True)], w=8,
             thr=BAD_ABOVE_ZERO),
        stat("Lowest NVMe spare", [q("min(nvme_available_spare_ratio) * 100", instant=True)], w=8,
             unit="percent", decimals=0,
             thr=thresholds(("red", None), ("orange", 10), ("yellow", 30), ("green", 50))),
        stat("SMART self-assessments failing",
             [q("count(smartmon_device_smart_healthy == 0"
                " and on (host, disk) smartmon_device_smart_available == 1) or vector(0)", instant=True)],
             w=8, thr=BAD_ABOVE_ZERO),
    ])

    g.section("Filesystems")
    g.add(joined_table(
        "Filesystem headroom",
        [("A", FS_KEY_A % inv.fs_used_pct(), "Used",
          [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge()),
         ("B", FS_KEY % ("node_filesystem_avail_bytes{%s}" % FS), "Free",
          [("unit", "bytes"), ("decimals", 1)]),
         ("C", FS_KEY % ("node_filesystem_size_bytes{%s}" % FS), "Size",
          [("unit", "bytes"), ("decimals", 1)]),
         ("D", FS_KEY % ("100 * (1 - node_filesystem_files_free{%s} / node_filesystem_files{%s})" % (FS, FS)),
          "Inodes", [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge()),
         ("E", FS_KEY % ("predict_linear(node_filesystem_avail_bytes{%s}[6h], 30 * 86400)" % FS), "Free in 30d",
          [("unit", "bytes"), ("decimals", 1), CELL_COLOR_TEXT,
           ("thresholds", thresholds(("red", None), ("orange", 1), ("green", 5e9)))])],
        h=14, join_on="fs", keep=r"^(host|mountpoint|device|fstype|Value #.*)$", sort=("Used", True),
        extra_overrides=[
            by_name("host", [("displayName", "Host"), ("custom.width", 150), HOST_LINK]),
            by_name("mountpoint", [("displayName", "Mount"), ("custom.width", 180)]),
            by_name("device", [("displayName", "Device")]),
            by_name("fstype", [("displayName", "Type"), ("custom.width", 90)])]))
    g.add(timeseries(
        "Filesystem fill · top 8",
        [q("topk(8, %s)" % inv.fs_used_pct(), "{{host}} {{mountpoint}}")],
        w=24, h=9, unit="percent", maxv=100, thr=PCT_USED, thr_style="dashed"))

    g.section("Disk I/O")
    g.extend([
        timeseries("Disk throughput · top 8",
                   [q("topk(8, rate(node_disk_read_bytes_total{%s}[$__rate_interval]))" % DISK,
                      "{{host}} {{device}} read"),
                    q("topk(8, rate(node_disk_written_bytes_total{%s}[$__rate_interval]))" % DISK,
                      "{{host}} {{device}} write", ref="B")],
                   unit="Bps", h=9),
        timeseries("Disk utilisation · top 8",
                   [q("topk(8, rate(node_disk_io_time_seconds_total{%s}[$__rate_interval]) * 100)" % DISK,
                      "{{host}} {{device}}")],
                   unit="percent", maxv=100, h=9, thr=PCT_LOAD),
    ])

    g.section("NVMe")
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
        extra_overrides=[by_name("host", [("displayName", "Host"), ("custom.width", 160), HOST_LINK]),
                         by_name("device", [("displayName", "Device"), ("custom.width", 120)])]))
    g.extend([
        timeseries("NVMe temperature", [q("nvme_temperature_celsius * 9 / 5 + 32", "{{host}} {{device}}")],
                   unit="fahrenheit", h=9, thr=TEMP_F, thr_style="dashed", min_zero=False),
        bargauge("Endurance used", [q("nvme_percentage_used_ratio * 100", "{{host}} {{device}}", instant=True)],
                 h=9),
    ])

    g.section("SATA drives")
    g.add(joined_table(
        "SMART",
        [("A", DK_KEY_A % ("smartmon_device_smart_healthy" + SMART_OK), "Healthy",
          [CELL_COLOR_BG, ("mappings", mapping({0: ("FAILING", "red"), 1: ("PASSED", "green")})),
           ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 100)]),
         ("B", DK_KEY % "((smartmon_temperature_celsius_raw_value"
                        " or smartmon_airflow_temperature_cel_raw_value) * 9 / 5 + 32)", "Temp",
          [("unit", "fahrenheit"), ("decimals", 0), ("thresholds", TEMP_F), CELL_COLOR_TEXT]),
         ("C", DK_KEY % "smartmon_power_on_hours_raw_value", "Powered on",
          [("unit", "h"), ("decimals", 0)]),
         ("D", DK_KEY % "smartmon_power_cycle_count_raw_value", "Power cycles", [("decimals", 0)]),
         ("E", DK_KEY % "smartmon_reallocated_sector_ct_raw_value", "Reallocated",
          [("decimals", 0), CELL_COLOR_TEXT, ("thresholds", BAD_ABOVE_ZERO)]),
         ("F", DK_KEY % "smartmon_current_pending_sector_raw_value", "Pending",
          [("decimals", 0), CELL_COLOR_TEXT, ("thresholds", BAD_ABOVE_ZERO)]),
         ("G", DK_KEY % "smartmon_udma_crc_error_count_raw_value", "CRC errors",
          [("decimals", 0), CELL_COLOR_TEXT, ("thresholds", BAD_ABOVE_ZERO)])],
        w=24, h=8, join_on="dk", keep=r"^(host|disk|Value #.*)$", sort=("Powered on", True),
        extra_overrides=[by_name("host", [("displayName", "Host"), ("custom.width", 160), HOST_LINK]),
                         by_name("disk", [("displayName", "Disk"), ("custom.width", 120)])]))

    g.section("ZFS")
    g.extend([
        stat("Pool state",
             [q('max(node_zfs_zpool_state{state="online",host="grey-server"})', instant=True)], w=8, h=6,
             mappings=mapping({0: ("NOT ONLINE", "red"), 1: ("ONLINE", "green")}),
             thr=GOOD_ABOVE_ZERO, text_mode="value"),
        timeseries("ARC size", [q('node_zfs_arc_size{host="grey-server"}', "arc")],
                   w=8, h=6, unit="bytes", tint="storage"),
        timeseries("ARC hit ratio",
                   [q('100 * rate(node_zfs_arc_hits{host="grey-server"}[$__rate_interval])'
                      ' / clamp_min(rate(node_zfs_arc_hits{host="grey-server"}[$__rate_interval])'
                      ' + rate(node_zfs_arc_misses{host="grey-server"}[$__rate_interval]), 1)', "hit ratio")],
                   w=8, h=6, unit="percent", maxv=100, tint="storage",
                   thr=thresholds(("red", None), ("orange", 80), ("green", 95))),
    ])

    return dashboard(
        "storage-health", "Storage & Drive Health", g,
        tags=["homelab", "storage"],
        description="Capacity first, then the drives underneath it: NVMe, SATA SMART, and ZFS.",
        refresh="1m", time_from="now-24h")


# ==================================================================== Network

def network():
    g = Grid()

    g.section("Right now")
    g.extend([
        stat("Fleet inbound",
             [q("sum(rate(node_network_receive_bytes_total{%s}[$__rate_interval]))" % NET, instant=True)],
             w=8, unit="Bps", decimals=1),
        stat("Fleet outbound",
             [q("sum(rate(node_network_transmit_bytes_total{%s}[$__rate_interval]))" % NET, instant=True)],
             w=8, unit="Bps", decimals=1),
        stat("Interfaces down",
             [q("count(node_network_up{%s} == 0) or vector(0)" % NET, instant=True)], w=8,
             thr=thresholds(("green", None), ("yellow", 1)),
             desc="Configured interfaces with no carrier. Unused wireless adapters, a spare "
                  "NIC on grey-server and a tunnel device sit here permanently."),
        stat("Errors and drops, last hour",
             [q("sum(increase(node_network_receive_errs_total{%s}[1h]))"
                " + sum(increase(node_network_transmit_errs_total{%s}[1h]))"
                " + sum(increase(node_network_receive_drop_total{%s}[1h]))"
                " + sum(increase(node_network_transmit_drop_total{%s}[1h])) or vector(0)" % (NET, NET, NET, NET),
                instant=True)],
             w=8, decimals=0, thr=thresholds(("green", None), ("yellow", 900), ("orange", 2000)),
             desc="Receive drops on the five hypervisor NICs run near 600 an hour as a steady "
                  "state. Errors are separate and are zero fleet-wide."),
        stat("Busiest conntrack table",
             [q("max(node_nf_conntrack_entries / node_nf_conntrack_entries_limit * 100)", instant=True)],
             w=8, unit="percent", decimals=1, thr=PCT_USED),
        stat("TCP retransmit rate",
             [q("sum(rate(node_netstat_Tcp_RetransSegs[$__rate_interval]))", instant=True)],
             w=8, unit="pps", decimals=2, thr=thresholds(("green", None), ("yellow", 10), ("orange", 100))),
    ])

    g.section("Throughput")
    g.extend([
        timeseries("Inbound · top 8",
                   [q("topk(8, sum by (host) (rate(node_network_receive_bytes_total{%s}[$__rate_interval])))" % NET,
                      "{{host}}")], unit="Bps", h=9),
        timeseries("Outbound · top 8",
                   [q("topk(8, sum by (host) (rate(node_network_transmit_bytes_total{%s}[$__rate_interval])))" % NET,
                      "{{host}}")], unit="Bps", h=9),
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

    g.section("Errors and drops")
    g.add(empty_ok(table(
        "Interfaces dropping or erroring, last hour",
        [tq("sum by (host, device) ("
            "increase(node_network_receive_errs_total{%s}[1h])"
            " + increase(node_network_transmit_errs_total{%s}[1h])"
            " + increase(node_network_receive_drop_total{%s}[1h])"
            " + increase(node_network_transmit_drop_total{%s}[1h])) > 0" % (NET, NET, NET, NET))],
        w=12, h=9, no_value="No errors or drops in the last hour",
        transformations=[
            {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(host|device|Value)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                {"host": "Host", "device": "Interface", "Value": "Packets"},
             "indexByName": {"host": 0, "device": 1, "Value": 2}}}],
        sort=("Packets", True),
        overrides=[by_name("Packets", [("decimals", 0), CELL_COLOR_TEXT,
                                       ("thresholds", thresholds(("yellow", None), ("orange", 100), ("red", 10000)))])])))
    g.add(timeseries(
        "Drops · top 8 interfaces",
        [q("topk(8, sum by (host, device) ("
           "rate(node_network_receive_drop_total{%s}[$__rate_interval])"
           " + rate(node_network_transmit_drop_total{%s}[$__rate_interval])))" % (NET, NET),
           "{{host}} {{device}}")],
        w=12, h=9, unit="pps", thr=thresholds(("green", None), ("orange", 1))))

    g.section("TCP and connection tracking")
    g.extend([
        timeseries("Established connections · top 8",
                   [q("topk(8, sum by (host) (node_netstat_Tcp_CurrEstab))", "{{host}}")], h=9),
        timeseries("Retransmits · top 8",
                   [q("topk(8, sum by (host) (rate(node_netstat_Tcp_RetransSegs[$__rate_interval])))", "{{host}}")],
                   unit="pps", h=9, thr=thresholds(("green", None), ("yellow", 1), ("orange", 20))),
        bargauge("Conntrack table used",
                 [q("node_nf_conntrack_entries / node_nf_conntrack_entries_limit * 100", "{{host}}", instant=True)],
                 w=12, h=9),
        timeseries("Sockets in use · top 8",
                   [q("topk(8, node_sockstat_TCP_inuse)", "{{host}} TCP"),
                    q("topk(8, node_sockstat_UDP_inuse)", "{{host}} UDP", ref="B")],
                   w=12, h=9),
    ])

    return dashboard(
        "network", "Network", g,
        tags=["homelab", "network"],
        description="Host-side networking: throughput, errors, TCP state and connection tracking. "
                    "Switches and access points are not in here.",
        refresh="30s", time_from="now-6h")


# ================================================================ Power / UPS

# nut_load and nut_battery_charge are ratios in the range 0..1, not percentages.
# Multiplying by the nominal VA rating turns load into watts: 0.27 x 900 = 243 W.
def power():
    g = Grid()
    ups = 'ups=~"$ups"'

    g.section("Right now")
    g.extend([
        stat("Mains", [q('nut_ups_status{status="OL", %s}' % ups, "{{ups}}", instant=True)], w=8,
             mappings=mapping({0: ("ON BATTERY", "red"), 1: ("ON MAINS", "green")}),
             thr=GOOD_ABOVE_ZERO, text_mode="value_and_name"),
        stat("Battery charge", [q("nut_battery_charge{%s} * 100" % ups, "{{ups}}", instant=True)], w=8,
             unit="percent", decimals=0, maxv=100,
             thr=thresholds(("red", None), ("orange", 30), ("yellow", 60), ("green", 90)),
             text_mode="value_and_name"),
        stat("Runtime left", [q("nut_battery_runtime_seconds{%s}" % ups, "{{ups}}", instant=True)], w=8,
             unit="s", decimals=0,
             thr=thresholds(("red", None), ("orange", 300), ("yellow", 900), ("green", 1800)),
             text_mode="value_and_name"),
        stat("Load", [q("nut_load{%s} * 100" % ups, "{{ups}}", instant=True)], w=8,
             unit="percent", decimals=0, maxv=100, thr=PCT_LOAD, text_mode="value_and_name"),
        stat("Draw", [q("nut_load{%s} * nut_real_power_nominal_watts{%s}" % (ups, ups), "{{ups}}", instant=True)],
             w=8, unit="watt", decimals=0, text_mode="value_and_name",
             desc="Load share times the 900 W nominal rating, as the UPS estimates it."),
        stat("Input voltage", [q("nut_input_voltage_volts{%s}" % ups, "{{ups}}", instant=True)], w=8,
             unit="volt", decimals=0, text_mode="value_and_name",
             thr=thresholds(("red", None), ("orange", 100), ("green", 110), ("orange", 130), ("red", 140))),
    ])

    g.section("Battery")
    g.extend([
        bargauge("Charge", [q("nut_battery_charge{%s} * 100" % ups, "{{ups}}", instant=True)],
                 w=12, h=7, thr=thresholds(("red", None), ("orange", 30), ("yellow", 60), ("green", 90))),
        bargauge("Runtime remaining", [q("nut_battery_runtime_seconds{%s}" % ups, "{{ups}}", instant=True)],
                 w=12, h=7, unit="s", maxv=3600, decimals=0,
                 thr=thresholds(("red", None), ("orange", 300), ("yellow", 900), ("green", 1800))),
        timeseries("Charge over time", [q("nut_battery_charge{%s} * 100" % ups, "{{ups}}")],
                   w=12, h=9, unit="percent", maxv=100),
        timeseries("Runtime over time", [q("nut_battery_runtime_seconds{%s}" % ups, "{{ups}}")],
                   w=12, h=9, unit="s"),
        timeseries("Battery voltage", [q("nut_battery_voltage_volts{%s}" % ups, "{{ups}}")],
                   w=24, h=8, unit="volt", min_zero=False),
    ])

    g.section("Load and mains")
    g.extend([
        bargauge("Load", [q("nut_load{%s} * 100" % ups, "{{ups}}", instant=True)], w=12, h=7, thr=PCT_LOAD),
        bargauge("Estimated draw",
                 [q("nut_load{%s} * nut_real_power_nominal_watts{%s}" % (ups, ups), "{{ups}}", instant=True)],
                 w=12, h=7, unit="watt", maxv=900, decimals=0,
                 thr=thresholds(("green", None), ("yellow", 630), ("orange", 765), ("red", 855))),
        timeseries("Load over time", [q("nut_load{%s} * 100" % ups, "{{ups}}")],
                   w=12, h=9, unit="percent", maxv=100, thr=PCT_LOAD),
        timeseries("Input voltage",
                   [q("nut_input_voltage_volts{%s}" % ups, "{{ups}}"),
                    q("nut_input_transfer_low_volts{%s}" % ups, "{{ups}} transfer low", ref="B"),
                    q("nut_input_transfer_high_volts{%s}" % ups, "{{ups}} transfer high", ref="C")],
                   w=12, h=9, unit="volt", min_zero=False,
                   overrides=[by_regex(".*transfer.*", [("custom.lineStyle", {"fill": "dash", "dash": [8, 6]}),
                                                        ("custom.lineWidth", 1),
                                                        ("color", fixed("text"))])]),
    ])

    g.section("Status history")
    g.add(state_timeline(
        "UPS status flags", [q("nut_ups_status{%s} == 1" % ups, "{{ups}} {{status}}")], h=9,
        mappings=mapping({1: ("set", "green")}), legend=LEGEND_LIST,
        desc="OL on line, OB on battery, LB low battery, CHRG charging, RB replace battery."))
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
        description="UPS-02 over the NUT protocol. Load and charge arrive as ratios and are scaled "
                    "to percentages here.",
        refresh="1m", time_from="now-24h",
        templating=[var_query("ups", "UPS", "label_values(nut_status, ups)")])


# ========================================================== Monitoring health

def monitoring():
    g = Grid()

    g.section("Scraping")
    g.extend([
        stat("Targets up", [q("count(up == 1)", instant=True)], w=8),
        stat("Targets down", [q("count(up == 0) or vector(0)", instant=True)], w=8,
             thr=BAD_ABOVE_ZERO),
        stat("Slowest scrape", [q("max(scrape_duration_seconds)", instant=True)], w=8,
             unit="s", decimals=2,
             thr=thresholds(("green", None), ("yellow", 1), ("orange", 5), ("red", 10))),
        stat("Samples ingested",
             [q("sum(rate(prometheus_tsdb_head_samples_appended_total[$__rate_interval]))", instant=True)],
             w=8, unit="wps", decimals=0),
        stat("Active series", [q("prometheus_tsdb_head_series", instant=True)], w=8,
             decimals=0,
             thr=thresholds(("green", None), ("yellow", 500000), ("orange", 1000000))),
        stat("TSDB on disk", [q("sum(prometheus_tsdb_storage_blocks_bytes)", instant=True)], w=8,
             unit="bytes", decimals=1),
    ])

    g.section("Targets")
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
        extra_overrides=[by_name("instance", [("displayName", "Target"), ("custom.width", 260)]),
                         by_name("job", [("displayName", "Job"), ("custom.width", 120)]),
                         by_name("host", [("displayName", "Host"), ("custom.width", 150), HOST_LINK])]))
    g.extend([
        timeseries("Scrape duration by job",
                   [q("max by (job) (scrape_duration_seconds)", "{{job}}")], h=9, unit="s"),
        timeseries("Samples scraped by job",
                   [q("sum by (job) (scrape_samples_scraped)", "{{job}}")], h=9, stack=True),
    ])

    g.section("Storage")
    g.extend([
        timeseries("Active series", [q("prometheus_tsdb_head_series", "head series")], h=9, w=8),
        timeseries("Ingestion rate",
                   [q("sum(rate(prometheus_tsdb_head_samples_appended_total[$__rate_interval]))", "samples/s")],
                   h=9, w=8, unit="wps"),
        timeseries("Block storage",
                   [q("prometheus_tsdb_storage_blocks_bytes", "on disk")], h=9, w=8, unit="bytes",
                   tint="storage"),
        timeseries("Compactions and truncations",
                   [q("increase(prometheus_tsdb_compactions_total[$__rate_interval])", "compactions"),
                    q("increase(prometheus_tsdb_wal_truncations_total[$__rate_interval])",
                      "WAL truncations", ref="B")],
                   h=8, w=12, decimals=0),
        timeseries("Query duration",
                   [q("prometheus_engine_query_duration_seconds{quantile=\"0.99\"}", "{{slice}} p99")],
                   h=8, w=12, unit="s"),
    ])

    g.section("Exporters")
    g.add(joined_table(
        "node_exporter fleet",
        [("A", 'max by (host, role) (up{job="node"})', "Up",
          [CELL_COLOR_BG, ("mappings", MAP_UP_DOWN), ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 70)]),
         ("B", "max by (host, version) (node_exporter_build_info)", "Build",
          [("custom.hidden", True)]),
         ("C", 'max by (host) (scrape_duration_seconds{job="node"})', "Scrape",
          [("unit", "s"), ("decimals", 3)] + cell_gauge(0, 2)),
         ("D", 'count by (host) (node_scrape_collector_success{collector!~"%s"} == 0)' % NO_COLLECTOR,
          "Collectors inactive",
          [("decimals", 0), CELL_COLOR_TEXT, ("noValue", "0"),
           ("thresholds", thresholds(("green", None), ("yellow", 8)))]),
         ("E", "max by (host) (abs(node_timex_offset_seconds))", "Clock offset",
          [("unit", "s"), ("decimals", 6), CELL_COLOR_TEXT,
           ("thresholds", thresholds(("green", None), ("yellow", 0.05), ("orange", 0.5)))]),
         ("F", "count by (host) (node_systemd_unit_state{state=\"failed\"} == 1)", "Failed units",
          [("decimals", 0), CELL_COLOR_TEXT, ("noValue", "0"), ("thresholds", thresholds(("green", None), ("orange", 1)))]),
         ("G", "sum by (host) (apt_upgrades_pending)", "Updates",
          [("decimals", 0), ("noValue", "—"), CELL_COLOR_TEXT,
           ("thresholds", thresholds(("green", None), ("yellow", 1), ("orange", 20)))])],
        h=14, sort=("Collectors inactive", True),
        keep=r"^(host|role|version|Value #.*)$", exclude=["Value #B"], index={"version": 2},
        extra_overrides=[by_name("host", [("displayName", "Host"), ("custom.width", 160), HOST_LINK]),
                         by_name("version", [("displayName", "Version"), ("custom.width", 110)]),
                         by_name("role", [("displayName", "Role"), ("custom.width", 120)])]))
    g.add(empty_ok(table(
        "Failed systemd units",
        [tq('node_systemd_unit_state{state="failed"} == 1')],
        w=12, h=9, no_value="No failed units",
        transformations=[
            {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(host|name)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName": {"host": "Host", "name": "Unit"},
                                           "indexByName": {"host": 0, "name": 1}}}],
        overrides=[by_name("Host", [("custom.width", 170), HOST_LINK])])))
    g.add(empty_ok(table(
        "Textfile collector errors",
        [tq("node_textfile_scrape_error != 0")],
        w=12, h=9, no_value="No collector errors",
        transformations=[
            {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(host|Value)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName": {"host": "Host", "Value": "Error"},
                                           "indexByName": {"host": 0, "Value": 1}}}],
        overrides=[by_name("Host", [("custom.width", 170), HOST_LINK])])))
    g.add(empty_ok(table(
        "Pending package updates",
        [tq("apt_upgrades_pending > 0")],
        w=24, h=9, no_value="No pending updates",
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
                    "the %d node_exporters." % len(inv.NODES),
        refresh="1m", time_from="now-6h")


# ================================================================== TeamSpeak

def teamspeak():
    g = Grid()
    s = 'server=~"$server"'

    g.section("Right now")
    g.extend([
        stat("Verdict", [q("teamspeak_server_fault{%s} * 2 + teamspeak_tunnel_fault{%s}" % (s, s),
                           "{{server}}", instant=True)], w=8, h=5,
             mappings=mapping({0: ("SERVING", "green"), 1: ("PUBLIC PATH DOWN", "orange"),
                               2: ("VOICE DOWN", "red"), 3: ("VOICE DOWN", "red")}),
             thr=thresholds(("green", None), ("orange", 1), ("red", 2)), text_mode="value_and_name"),
        stat("Public address", [q("teamspeak_public_up{%s}" % s, "{{server}}", instant=True)], w=8, h=5,
             mappings=MAP_UP_DOWN, thr=GOOD_ABOVE_ZERO,
             text_mode="value_and_name"),
        stat("Local voice", [q("teamspeak_local_up{%s}" % s, "{{server}}", instant=True)], w=8, h=5,
             mappings=MAP_UP_DOWN, thr=GOOD_ABOVE_ZERO,
             text_mode="value_and_name"),
        stat("Name resolution", [q("teamspeak_dns_srv_up{%s}" % s, "{{server}}", instant=True)], w=8, h=5,
             mappings=mapping({0: ("CANNOT RESOLVE", "red"), 1: ("RESOLVES", "green")}),
             thr=GOOD_ABOVE_ZERO, text_mode="value_and_name"),
        stat("ServerQuery", [q("teamspeak_query_up{%s}" % s, "{{server}}", instant=True)], w=8, h=5,
             mappings=MAP_OK_FAIL, thr=GOOD_ABOVE_ZERO,
             text_mode="value_and_name"),
        stat("Collector freshness", [q("time() - teamspeak_last_probe_timestamp_seconds", instant=True)],
             w=8, h=5, unit="s", decimals=0,
             thr=thresholds(("green", None), ("yellow", 120), ("orange", 300), ("red", 900))),
    ])

    g.section("Availability over time")
    g.add(state_timeline(
        "Reachability",
        [q("teamspeak_public_up{%s}" % s, "{{server}} public"),
         q("teamspeak_local_up{%s}" % s, "{{server}} local", ref="B"),
         q("teamspeak_dns_srv_up{%s}" % s, "{{server}} SRV record", ref="C")],
        h=9, mappings=mapping({0: ("down", "red"), 1: ("up", "green")}), legend=LEGEND_LIST))
    g.extend([
        stat("Public availability",
             [q("avg_over_time(teamspeak_public_up{%s}[$__range]) * 100" % s, "{{server}}", instant=True)],
             w=8, h=7, unit="percent", decimals=3,
             thr=thresholds(("red", None), ("orange", 99), ("yellow", 99.9), ("green", 99.99)),
             text_mode="value_and_name"),
        timeseries("Public round trip",
                   [q("teamspeak_public_rtt_seconds{%s} > 0" % s, "{{server}}")],
                   w=16, h=7, unit="s", decimals=3,
                   thr=thresholds(("green", None), ("yellow", 0.15), ("orange", 0.3))),
    ])

    g.section("The public path")
    g.add(table(
        "Relay endpoints",
        [tq("teamspeak_public_up{%s}" % s)],
        h=6,
        transformations=[
            {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(server|address|relay|Value)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                {"server": "Server", "address": "Public address", "relay": "Relay", "Value": "Up"},
             "indexByName": {"server": 0, "address": 1, "relay": 2, "Value": 3}}}],
        overrides=[by_name("Up", [CELL_COLOR_BG, ("mappings", MAP_UP_DOWN),
                                  ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 80)]),
                   by_name("Relay", [CELL_COLOR_TEXT,
                                     ("mappings", [{"type": "regex", "options": {"pattern": "^unresolved.*",
                                                                                 "result": {"text": "unresolved",
                                                                                            "color": "red", "index": 0}}}])])]))

    g.section("Server statistics")
    g.extend([
        stat("Clients online", [q("teamspeak_clients_online{%s}" % s, "{{server}}", instant=True)],
             w=6, h=5, text_mode="value_and_name"),
        stat("Channels", [q("teamspeak_channels_online{%s}" % s, "{{server}}", instant=True)],
             w=6, h=5, text_mode="value_and_name"),
        stat("Slots", [q("teamspeak_max_clients{%s}" % s, "{{server}}", instant=True)],
             w=6, h=5, text_mode="value_and_name"),
        stat("Virtual server uptime", [q("teamspeak_uptime_seconds{%s}" % s, "{{server}}", instant=True)],
             w=6, h=5, unit="s", decimals=0, text_mode="value_and_name"),
        timeseries("Clients online", [q("teamspeak_clients_online{%s}" % s, "{{server}}")],
                   w=24, h=9, decimals=0),
    ])

    g.section("Collector")
    g.extend([
        timeseries("Collection duration", [q("teamspeak_probe_duration_seconds", "duration")],
                   w=12, h=8, unit="s", decimals=2),
        timeseries("Local round trip", [q("teamspeak_local_rtt_seconds{%s} > 0" % s, "{{server}}")],
                   w=12, h=8, unit="s", decimals=4),
    ])

    return dashboard(
        "teamspeak", "TeamSpeak", g,
        tags=["homelab", "teamspeak"],
        description="Voice reachability for ts02 and ts03, public and local.",
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
        where += " on %s" % n["pve"]

    # /proc/uptime is not namespaced, so an LXC reports its node's boot time.
    # Proxmox publishes the guest's own; the hypervisors keep node_exporter's.
    if kind == "lxc":
        up_expr = 'pve_uptime_seconds{id="%s"}' % n["vmid"]
        boot_expr = '(time() - pve_uptime_seconds{id="%s"}) * 1000' % n["vmid"]
    else:
        up_expr = "time() - node_boot_time_seconds{%s}" % H
        boot_expr = "node_boot_time_seconds{%s} * 1000" % H

    g.section("Status")
    tiles = [
        stat("Reachable", [q('up{job="node", %s}' % H, instant=True)], w=6,
             mappings=MAP_UP_DOWN, thr=GOOD_ABOVE_ZERO, text_mode="value"),
        stat("Uptime", [q(up_expr, instant=True)], w=6,
             unit="s", decimals=0),
        stat("CPU busy", [q(inv.CPU_BUSY % (", " + H, ", " + H), instant=True)], w=6,
             unit="percent", decimals=1, thr=PCT_LOAD),
        stat("Load per core",
             [q("node_load1{%s} / on (host) group_left () %s" % (H, inv.CORES % (", " + H)),
                instant=True)], w=6,
             decimals=2, thr=LOAD_PER_CORE, desc="One-minute load divided by core count."),
        stat("Memory used", [q(inv.MEM_USED % (H, H), instant=True)], w=6,
             unit="percent", decimals=1, thr=PCT_USED,
             desc="Against MemAvailable, so page cache counts as free."),
        stat("Swap in use",
             [q("node_memory_SwapTotal_bytes{%s} - node_memory_SwapFree_bytes{%s}" % (H, H), instant=True)],
             w=6, unit="bytes", decimals=1,
             thr=thresholds(("green", None), ("yellow", 1), ("orange", 1073741824))),
        stat("Root filesystem", [q(inv.fs_used_pct(sel(H, 'mountpoint="/"')), instant=True)], w=6,
             unit="percent", decimals=1, thr=PCT_USED),
    ]
    if n["temp"]:
        tiles.append(stat("CPU package", [q("max(%s)" % (PKG_TEMP_F % H), instant=True)], w=6,
                          unit="fahrenheit", decimals=0, thr=TEMP_F))
    else:
        tiles.append(stat("Processes running", [q("node_procs_running{%s}" % H, instant=True)], w=6,
                          decimals=0))
    g.extend(tiles)

    # ---------------------------------------------------------------- CPU
    g.section("CPU")
    cpu_panels = [
        timeseries("CPU by mode",
                   [q("sum by (mode) (rate(node_cpu_seconds_total{%s, mode!=\"idle\"}[$__rate_interval]))"
                      " / on () group_left () count(count by (cpu) (node_cpu_seconds_total{%s})) * 100" % (H, H),
                      "{{mode}}")],
                   unit="percent", h=9, stack=True, maxv=100,
                   desc="Normalised to one core, so the stack tops out at 100%."),
        timeseries("Load average",
                   [q("node_load1{%s}" % H, "1 minute"),
                    q("node_load5{%s}" % H, "5 minutes", ref="B"),
                    q("node_load15{%s}" % H, "15 minutes", ref="C"),
                    q(inv.CORES % (", " + H), "cores", ref="D")],
                   h=9, decimals=2,
                   overrides=[by_name("cores", [("custom.lineStyle", {"fill": "dash", "dash": [8, 6]}),
                                                ("custom.lineWidth", 1), ("color", fixed("text"))])]),
    ]
    if n["psi"]:
        cpu_panels.append(timeseries(
            "CPU pressure",
            [q("rate(node_pressure_cpu_waiting_seconds_total{%s}[$__rate_interval]) * 100" % H, "some")],
            h=8, unit="percent", maxv=100, tint="compute",
            thr=thresholds(("green", None), ("yellow", 10), ("orange", 30))))
    if n["cpufreq"]:
        cpu_panels.append(timeseries(
            "Clock speed", [q("node_cpu_scaling_frequency_hertz{%s}" % H, "core {{cpu}}")],
            h=8, unit="hertz", legend=LEGEND_LIST, min_zero=False))
    for i, p in enumerate(cpu_panels):
        p["gridPos"]["w"] = 12
    g.extend(cpu_panels)

    # ------------------------------------------------------------- Memory
    g.section("Memory")
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
                   w=12, h=9, unit="bytes", stack=True, overrides=mem_overrides),
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
            w=12, h=8, unit="percent", maxv=100, tint="memory",
            thr=thresholds(("green", None), ("yellow", 1), ("orange", 10))))
    mem_panels.append(timeseries(
        "Major page faults",
        [q("rate(node_vmstat_pgmajfault{%s}[$__rate_interval])" % H, "major faults/s")],
        w=12, h=8, unit="reqps", tint="memory"))
    g.extend(mem_panels)

    # -------------------------------------------------------- Filesystems
    g.section("Filesystems")
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
    # /proc/diskstats is not namespaced, so an LXC reports its node's block
    # devices and its node's traffic on them. Say so rather than imply the
    # container owns these numbers; the section is gated only by naming.
    g.section("Node disk" if kind == "lxc" else "Disk")
    D = sel(DISK, H)
    disk_note = ("An LXC shares its node's /proc/diskstats, so these are the hypervisor's block "
                 "devices and its traffic on them, not this container's.") if kind == "lxc" else ""
    disk_panels = [
        timeseries("Throughput",
                   [q("rate(node_disk_read_bytes_total{%s}[$__rate_interval])" % D, "{{device}} read"),
                    q("-1 * rate(node_disk_written_bytes_total{%s}[$__rate_interval])" % D,
                      "{{device}} write", ref="B")],
                   w=12, h=9, unit="Bps", min_zero=False, desc=disk_note),
        timeseries("Operations",
                   [q("rate(node_disk_reads_completed_total{%s}[$__rate_interval])" % D, "{{device}} read"),
                    q("-1 * rate(node_disk_writes_completed_total{%s}[$__rate_interval])" % D,
                      "{{device}} write", ref="B")],
                   w=12, h=9, unit="iops", min_zero=False),
        timeseries("Utilisation",
                   [q("rate(node_disk_io_time_seconds_total{%s}[$__rate_interval]) * 100" % D, "{{device}}")],
                   w=12, h=8, unit="percent", maxv=100, thr=PCT_LOAD),
    ]
    if n["psi"]:
        disk_panels.append(timeseries(
            "I/O pressure",
            [q("rate(node_pressure_io_waiting_seconds_total{%s}[$__rate_interval]) * 100" % H, "some")],
            w=12, h=8, unit="percent", maxv=100, tint="storage",
            thr=thresholds(("green", None), ("yellow", 10), ("orange", 30))))
    else:
        disk_panels.append(timeseries(
            "Queue time",
            [q("rate(node_disk_io_time_weighted_seconds_total{%s}[$__rate_interval])" % D, "{{device}}")],
            w=12, h=8, unit="s"))
    g.extend(disk_panels)

    # ------------------------------------------------------------ Network
    g.section("Network")
    N = sel(NET, H)
    net_panels = [
        timeseries("Throughput",
                   [q("rate(node_network_receive_bytes_total{%s}[$__rate_interval])" % N, "{{device}} in"),
                    q("-1 * rate(node_network_transmit_bytes_total{%s}[$__rate_interval])" % N,
                      "{{device}} out", ref="B")],
                   w=12, h=9, unit="Bps", min_zero=False),
        timeseries("Errors and drops",
                   [q("rate(node_network_receive_errs_total{%s}[$__rate_interval])" % N, "{{device}} in errors"),
                    q("rate(node_network_transmit_errs_total{%s}[$__rate_interval])" % N, "{{device}} out errors", ref="B"),
                    q("rate(node_network_receive_drop_total{%s}[$__rate_interval])" % N, "{{device}} in drops", ref="C"),
                    q("rate(node_network_transmit_drop_total{%s}[$__rate_interval])" % N, "{{device}} out drops", ref="D")],
                   w=12, h=9, unit="pps", thr=thresholds(("green", None), ("orange", 1))),
        timeseries("TCP connections",
                   [q("node_netstat_Tcp_CurrEstab{%s}" % H, "established"),
                    q("node_sockstat_TCP_tw{%s}" % H, "time-wait", ref="B")],
                   w=12, h=8, decimals=0),
        timeseries("TCP retransmits",
                   [q("rate(node_netstat_Tcp_RetransSegs{%s}[$__rate_interval])" % H, "retransmitted"),
                    q("rate(node_netstat_Tcp_OutSegs{%s}[$__rate_interval])" % H, "sent", ref="B")],
                   w=12, h=8, unit="pps"),
    ]
    if n["conntrack"]:
        net_panels.append(gauge(
            "Connection tracking table",
            [q("node_nf_conntrack_entries{%s} / node_nf_conntrack_entries_limit{%s} * 100" % (H, H), instant=True)],
            w=8, h=8))
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
            w=24, h=8, decimals=0))
    g.extend(net_panels)

    # ----------------------------------------------------------- Hardware
    if n["temp"] or n["nvme"] or n["smart"] or n["zfs"]:
        g.section("Hardware")
    if n["temp"]:
        g.add(timeseries(
            "Temperatures",
            [q("%s" % (PKG_TEMP_F % H), "package"),
             q("node_hwmon_temp_celsius{%s} * on (host, chip, sensor) group_left (label)"
               " node_hwmon_sensor_label{label=~\"Core .*|Tccd.*\"} * 9 / 5 + 32" % H, "{{label}}", ref="B")],
            w=24, h=9, unit="fahrenheit", thr=TEMP_F, thr_style="dashed", min_zero=False))
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
            extra_overrides=[by_name("disk", [("displayName", "Disk"), ("custom.width", 140)])]))
    if n["zfs"]:
        g.add(stat("ZFS pool state",
                   [q('max by (zpool) (node_zfs_zpool_state{state="online", %s})' % H, "{{zpool}}", instant=True)],
                   w=8, h=7, mappings=mapping({0: ("NOT ONLINE", "red"), 1: ("ONLINE", "green")}),
                   thr=GOOD_ABOVE_ZERO, text_mode="value_and_name"))
        g.add(timeseries("ZFS ARC size", [q("node_zfs_arc_size{%s}" % H, "ARC")],
                         w=8, h=7, unit="bytes", tint="storage"))
        g.add(timeseries("ZFS ARC hit ratio",
                         [q("100 * rate(node_zfs_arc_hits{%s}[$__rate_interval]) / clamp_min("
                            "rate(node_zfs_arc_hits{%s}[$__rate_interval])"
                            " + rate(node_zfs_arc_misses{%s}[$__rate_interval]), 1)" % (H, H, H), "hit ratio")],
                         w=8, h=7, unit="percent", maxv=100, tint="storage",
                         thr=thresholds(("red", None), ("orange", 80), ("green", 95))))

    # ------------------------------------------------------------- Guests
    if kind == "metal":
        g.section("Guests on this node")
        on_node = ' and on (id) pve_guest_info{node="%s"}' % host
        g.add(empty_ok(joined_table(
            "Guests on %s" % host,
            [("A", 'pve_up{%s} * on (id) group_left (name, node, type) pve_guest_info{node="%s"}' % (GUEST, host), "Up",
              [CELL_COLOR_BG, ("mappings", MAP_UP_DOWN), ("thresholds", GOOD_ABOVE_ZERO), ("custom.width", 70)]),
             ("B", "pve_cpu_usage_ratio{%s} * 100%s" % (GUEST, on_node), "CPU",
              [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_LOAD)] + cell_gauge()),
             ("C", "pve_memory_usage_bytes{%s} / pve_memory_size_bytes{%s} * 100%s"
                   % (GUEST, GUEST, on_node), "Memory",
              [("unit", "percent"), ("decimals", 1), ("thresholds", PCT_USED)] + cell_gauge()),
             ("D", "pve_memory_size_bytes{%s}%s" % (GUEST, on_node), "RAM",
              [("unit", "bytes"), ("decimals", 0)]),
             ("E", "pve_disk_size_bytes{%s}%s" % (GUEST, on_node), "Disk",
              [("unit", "bytes"), ("decimals", 0)]),
             ("F", "pve_uptime_seconds{%s}%s" % (GUEST, on_node), "Uptime",
              [("unit", "s"), ("decimals", 0)])],
            w=24, h=9, join_on="id", keep=r"^(id|name|type|Value #.*)$", sort=("CPU", True),
            extra_overrides=[
                by_name("id", [("displayName", "ID"), ("custom.width", 90)]),
                by_name("name", [("displayName", "Guest"), ("custom.width", 180),
                                 ("links", [{"title": "Open this host's dashboard",
                                             "url": "/d/node-${__value.raw}", "targetBlank": False}])]),
                by_name("type", [("displayName", "Type"), ("custom.width", 80)])],
            no_value="No guests on this node")))
        g.add(empty_ok(timeseries(
            "Guest CPU on %s · top 8" % host,
            [q('topk(8, pve_cpu_usage_ratio{%s} * 100 * on (id) group_left () '
               'pve_guest_info{node="%s"})' % (GUEST, host), "{{id}}")],
            w=24, h=8, unit="percent", thr=PCT_LOAD)))

    # --------------------------------------------------------- Containers
    if n["docker"]:
        ct = sel(CT, H)
        g.section("Containers on this host")
        g.add(joined_table(
            "Containers",
            [("A", "sum by (name, image) (rate(container_cpu_usage_seconds_total{%s}[$__rate_interval])) * 100" % ct,
              "CPU", [("unit", "percent"), ("decimals", 2), ("thresholds", PCT_LOAD)] + cell_gauge(0, 200)),
             ("B", "sum by (name) (container_memory_working_set_bytes{%s})" % ct, "Memory",
              [("unit", "bytes"), ("decimals", 1)]),
             ("C", "max by (name) (time() - container_start_time_seconds{%s})" % ct, "Up for",
              [("unit", "s"), ("decimals", 0), CELL_COLOR_TEXT,
               ("thresholds", thresholds(("orange", None), ("green", 3600)))]),
             ("D", "sum by (name) (rate(container_network_receive_bytes_total{%s}[$__rate_interval]))"
                   % sel(ct, CT_IFACE), "Net in", [("unit", "Bps"), ("decimals", 1)]),
             ("E", "sum by (name) (rate(container_network_transmit_bytes_total{%s}[$__rate_interval]))"
                   % sel(ct, CT_IFACE), "Net out", [("unit", "Bps"), ("decimals", 1)])],
            w=24, h=10, join_on="name", keep=r"^(name|image|Value #.*)$", sort=("CPU", True),
            extra_overrides=[by_name("name", [("displayName", "Container"), ("custom.width", 220)]),
                             by_name("image", [("displayName", "Image")])]))
        g.add(timeseries(
            "Container CPU · top 10",
            [q("topk(10, sum by (name) (rate(container_cpu_usage_seconds_total{%s}[$__rate_interval])) * 100)" % ct,
               "{{name}}")], w=12, h=9, unit="percent"))
        g.add(timeseries(
            "Container memory · top 10",
            [q("topk(10, sum by (name) (container_memory_working_set_bytes{%s}))" % ct, "{{name}}")],
            w=12, h=9, unit="bytes"))

    # ---------------------------------------------------------------- UPS
    if n.get("ups"):
        u = n["ups"]
        g.section("Power")
        g.extend([
            stat("Mains", [q('nut_ups_status{status="OL", ups="%s"}' % u, instant=True)], w=6, h=5,
                 mappings=mapping({0: ("ON BATTERY", "red"), 1: ("ON MAINS", "green")}),
                 thr=GOOD_ABOVE_ZERO, text_mode="value"),
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
    g.section("Facts")
    g.extend([
        stat("Booted", [q(boot_expr, instant=True)], w=6, h=5,
             unit="dateTimeAsLocal", text_mode="value"),
        stat("Cores", [q(inv.CORES % (", " + H), instant=True)],
             w=6, h=5, decimals=0),
        stat("Total RAM", [q("node_memory_MemTotal_bytes{%s}" % H, instant=True)], w=6, h=5,
             unit="bytes", decimals=1),
        stat("Clock offset", [q("abs(node_timex_offset_seconds{%s})" % H, instant=True)], w=6, h=5,
             unit="s", decimals=6,
             thr=thresholds(("green", None), ("yellow", 0.05), ("orange", 0.5))),
    ])
    g.add(table(
        "Identity",
        [tq("node_uname_info{%s}" % H), tq("node_os_info{%s}" % H, ref="B"),
         tq('label_replace(node_exporter_build_info{%s}, "exporter_version", "$1", "version", "(.*)")' % H,
            ref="C")],
        w=24, h=4,
        transformations=[
            {"id": "joinByField", "options": {"byField": "host", "mode": "outer"}},
            {"id": "filterFieldsByName",
             "options": {"include": {"pattern": r"^(nodename|pretty_name|release|machine|exporter_version)$"}}},
            {"id": "organize", "options": {"excludeByName": {}, "renameByName":
                {"nodename": "Hostname", "pretty_name": "Operating system", "release": "Kernel",
                 "machine": "Architecture", "exporter_version": "node_exporter"},
             "indexByName": {"nodename": 0, "pretty_name": 1, "release": 2, "machine": 3,
                             "exporter_version": 4}}}]))
    if n["systemd"]:
        g.add(empty_ok(table(
            "Failed units on %s" % host,
            [tq('node_systemd_unit_state{state="failed", %s} == 1' % H)],
            w=12, h=7, no_value="No failed units",
            transformations=[
                {"id": "filterFieldsByName", "options": {"include": {"pattern": r"^(name)$"}}},
                {"id": "organize", "options": {"excludeByName": {}, "renameByName": {"name": "Unit"},
                                               "indexByName": {"name": 0}}}])))
    if n["apt"]:
        g.add(empty_ok(table(
            "Pending updates on %s" % host,
            [tq("apt_upgrades_pending{%s} > 0" % H)],
            w=12, h=7, no_value="No pending updates",
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
        description="%s · %s · role %s · %s." % (host, n["ip"], n["role"], where),
        refresh="30s", time_from="now-6h")


# ======================================================================= main

def main() -> int:
    OUT_TOPIC.mkdir(parents=True, exist_ok=True)
    OUT_NODES.mkdir(parents=True, exist_ok=True)

    topic = [overview(), proxmox(), containers(), services(), storage(),
             network(), power(), monitoring(), teamspeak(), uptime.build()]

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
                total += len(p.get("panels", []))
            else:
                total += 1
        return total

    print("%d dashboards" % written)
    for d in topic:
        print("  %-28s %-34s %3d panels" % (d["uid"], d["title"], count(d)))
    # A node board grows only the sections its host has data for, so the count
    # is a range, not one number. Printing NODES[0] read as if every board matched it.
    sizes = sorted(count(node_dashboard(n)) for n in inv.NODES)
    print("  %-28s %-34s %3d-%d panels (%d files)"
          % ("node-*", "one per host", sizes[0], sizes[-1], len(inv.NODES)))
    print("%d panel titles registered as allowed-empty" % len(ALLOW_EMPTY))
    return 0


if __name__ == "__main__":
    sys.exit(main())
