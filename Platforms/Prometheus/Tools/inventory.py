#!/usr/bin/env python3
"""What the fleet is, and the PromQL fragments that depend on knowing it.

The capability flags are not guesses. They were read off the live Prometheus on
2026-08-27 and they decide which sections a node dashboard grows: there is no
point drawing an NVMe row for a host with no NVMe, and an empty panel reads as
"nothing wrong" rather than "not applicable", which is worse than no panel.

`assert_dashboard_queries.py` is what keeps this honest. If a flag here stops
matching reality, the panel it generated goes empty and the assertion fails.
"""

# kind: metal    - a Proxmox node, owns its own hardware
#       qemu     - a full VM, owns virtual disks and its own kernel
#       lxc      - a container sharing the node's kernel, and therefore its
#                  /proc/diskstats, /sys/class/hwmon, ZFS and SMART views
NODES = [
    dict(host="grey-server",    role="hypervisor", ip="192.168.70.10", kind="metal",
         zfs=True,  nvme=False, smart=False, temp=True, ups="ups02", apt=False, docker=False),
    dict(host="purple-server",  role="hypervisor", ip="192.168.70.11", kind="metal",
         zfs=False, nvme=True,  smart=True,  temp=True, apt=True,  docker=False),
    dict(host="blue-server",    role="hypervisor", ip="192.168.70.12", kind="metal",
         zfs=False, nvme=True,  smart=True,  temp=True, apt=True,  docker=False),
    dict(host="red-server",     role="hypervisor", ip="192.168.70.13", kind="metal",
         zfs=False, nvme=True,  smart=True,  temp=True, apt=True, docker=False),
    dict(host="green-server",   role="hypervisor", ip="192.168.70.14", kind="metal",
         zfs=False, nvme=True,  smart=True,  temp=True, apt=True,  docker=False),

    dict(host="security-01",    role="security",   ip="192.168.72.2",  kind="qemu",
         pve="grey-server",  vmid="qemu/200", docker=True,  apt=False),
    dict(host="splunk-siem",    role="security",   ip="192.168.72.3",  kind="qemu",
         pve="grey-server",  vmid="qemu/109", docker=False, apt=False),
    dict(host="edge-01",        role="edge",       ip="192.168.30.10", kind="qemu",
         pve="grey-server",  vmid="qemu/121", docker=False, apt=False),
    dict(host="app-01",         role="app",        ip="192.168.80.10", kind="qemu",
         pve="grey-server",  vmid="qemu/116", docker=True,  apt=False),
    dict(host="alpha-prod-01",  role="app",        ip="192.168.80.118", kind="qemu",
         pve="grey-server",  vmid="qemu/401", docker=True,  apt=True, teamspeak=True),
    dict(host="ubuntu-dev",     role="workstation", ip="192.168.40.179", kind="qemu",
         pve="grey-server",  vmid="qemu/105", docker=False, apt=True),

    dict(host="ansible-01",     role="automation", ip="192.168.40.36", kind="lxc",
         pve="grey-server",  vmid="lxc/100",  docker=False, apt=True),
    dict(host="docker-main",    role="docker",     ip="192.168.40.35", kind="lxc",
         pve="grey-server",  vmid="lxc/110",  docker=True,  apt=False),
    dict(host="docker-blue",    role="docker",     ip="192.168.40.39", kind="lxc",
         pve="blue-server",  vmid="lxc/108",  docker=True,  apt=True),
    dict(host="docker-network", role="docker",     ip="192.168.85.2",  kind="lxc",
         pve="blue-server",  vmid="lxc/107",  docker=True,  apt=True),
    dict(host="media-01",       role="docker",     ip="192.168.40.42", kind="lxc",
         pve="red-server",   vmid="lxc/842",  docker=True,  apt=True),
    dict(host="monitor-01",     role="monitoring", ip="192.168.73.2",  kind="lxc",
         pve="blue-server",  vmid="lxc/104",  docker=True,  apt=True, prometheus=True),
    dict(host="game-01",        role="game",       ip="192.168.80.30", kind="lxc",
         pve="green-server", vmid="lxc/123",  docker=True,  apt=True),
]

BY_HOST = {n["host"]: n for n in NODES}
HYPERVISORS = [n["host"] for n in NODES if n["kind"] == "metal"]
UPS_BY_HOST = {n["host"]: n["ups"] for n in NODES if n.get("ups")}

WHAT_IS_IT = {
    "metal": "a Proxmox node, on its own hardware",
    "qemu":  "a KVM virtual machine",
    "lxc":   "an LXC container, sharing its node's kernel",
}

# ------------------------------------------------------------- label filters

# Pseudo-filesystems say nothing about capacity and would swamp every bar chart.
FS = ('fstype!~"tmpfs|devtmpfs|overlay|squashfs|fuse.*|nsfs|ramfs|autofs|iso9660|'
      'proc|sysfs|cgroup.*|debugfs|tracefs|mqueue|configfs|binfmt_misc|efivarfs"')

# Physical and bridge interfaces only. A Docker host carries a veth per container
# and a Proxmox node a fwbr/fwln/fwpr trio per guest; grey-server alone has 39
# interfaces, of which 6 mean anything.
NET = 'device!~"lo|veth.*|fw(br|pr|ln).*|tap.*|br-.*|docker.*|virbr.*|cali.*|nomad.*"'

# Real block devices. Excludes loop, device-mapper duplicates of the same IO, and
# the zd* ZFS volume nodes that double-count a pool's traffic.
DISK = 'device!~"loop.*|ram.*|dm-.*|zd.*|sr.*|fd.*"'

# cAdvisor reports the root cgroup with an empty name; it is the host, not a
# container, and including it makes every "top 10" chart a chart about the host.
CT = 'name!=""'

# ---------------------------------------------------------- shared PromQL

CORES = 'count by (host) (count by (host, cpu) (node_cpu_seconds_total{%s}))'
CPU_BUSY = ('100 - (avg by (host) (rate(node_cpu_seconds_total{mode="idle"%s}[$__rate_interval])) * 100)')
MEM_USED = ('100 * (1 - avg by (host) (node_memory_MemAvailable_bytes{%s})'
            ' / avg by (host) (node_memory_MemTotal_bytes{%s}))')

# Intel reports the die as coretemp "Package id 0"; AMD reports it as "Tctl" on a
# k10temp chip. Matching on the sensor label rather than the chip name covers
# both, which a chip=~".*coretemp.*" filter does not: it silently omits
# grey-server, the one AMD node in the fleet.
PKG_TEMP_F = ('node_hwmon_temp_celsius{%s} * on (host, chip, sensor) group_left (label)'
              ' node_hwmon_sensor_label{label=~"Package id 0|Tctl"} * 9 / 5 + 32')


def sel(*clauses) -> str:
    """Join non-empty label matchers into a selector body."""
    return ", ".join(c for c in clauses if c)


def host_sel(host: str) -> str:
    return 'host="%s"' % host


def fs_used_pct(extra: str = "") -> str:
    s = sel(FS, extra)
    return ('100 * (1 - node_filesystem_avail_bytes{%s} / node_filesystem_size_bytes{%s})' % (s, s))


# ------------------------------------------------- collector availability

# Read off the live Prometheus on 2026-08-27. These are not preferences: a panel
# built for a collector the host does not run draws an empty rectangle, and an
# empty rectangle on a dashboard reads as "fine" rather than "not applicable".
#
# splunk-siem runs Rocky 10 and has no /proc/pressure. edge-01 has no
# nf_conntrack module loaded. The systemd collector is enabled on twelve hosts.
# cpufreq and hwmon exist on the five nodes and the seven LXC guests, but on an
# LXC they are the node's, so the node dashboards only draw them on bare metal.
_NO_PSI = {"splunk-siem"}
_NO_CONNTRACK = {"edge-01"}
_SYSTEMD = {"alpha-prod-01", "ansible-01", "blue-server", "docker-blue", "docker-network",
            "game-01", "green-server", "media-01", "monitor-01", "purple-server",
            "red-server", "ubuntu-dev"}

for _n in NODES:
    _n.setdefault("apt", False)
    _n.setdefault("docker", False)
    _n.setdefault("zfs", False)
    _n.setdefault("nvme", False)
    _n.setdefault("smart", False)
    _n.setdefault("temp", False)
    _n["psi"] = _n["host"] not in _NO_PSI
    _n["conntrack"] = _n["host"] not in _NO_CONNTRACK
    _n["systemd"] = _n["host"] in _SYSTEMD
    _n["cpufreq"] = _n["kind"] == "metal"
del _n
