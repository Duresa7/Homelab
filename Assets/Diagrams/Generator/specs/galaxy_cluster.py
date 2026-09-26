#!/usr/bin/env python3
"""galaxy-cluster: five Proxmox VE nodes as columns with their hardware, storage
pools and guests, the two Corosync rings, and the UPS that feeds three nodes.
Node and guest facts: .scratch/reorg/BRIEF.md tables. UPS-02 assignment:
Infrastructure/Hardware/Power.md (grey, blue and red on UPS-02)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "galaxy-cluster.svg")
d = Diagram("galaxy-cluster", "Galaxy cluster: five Proxmox VE 9.2.11 nodes",
            "No shared storage and no HA groups. Corosync link0 rides MGMT-A (VLAN 70), link1 rides Cluster-Net (VLAN 71)",
            source="Infrastructure/Hardware/Nodes.md, Operations/Inventory/Galaxy/VMs.md and LXCs.md, Infrastructure/Hardware/Power.md",
            width=1640, card_w=190)

def node(id, title, ip, notes, cols=1):
    d.group(id, title, badge=ip, family="Mgmt", cols=cols, notes=notes, accent=id)

node("grey", "grey-server", "192.168.70.10", [("amd", "Ryzen 7 3700X, 8c/16t"), (None, "62.72 GiB memory"), ("nvidia", "GeForce GTX 1080 Ti"),
     (None, "NVMe 931 GiB · local-lvm"), (None, "SSD 1.82 TiB · ssd-lvm1"), (None, "HDD 1.82 TiB · hddpool-1 (ZFS)")], cols=3)
node("purple", "purple-server", "192.168.70.11", [("intel", "Core i5-8500T, 6c"), (None, "15.46 GiB memory"), (None, "integrated graphics"),
     (None, "NVMe 238 GiB"), (None, "SSD 232 GiB · ssd-lvm2 (empty)")])
node("blue", "blue-server", "192.168.70.12", [("intel", "Core i5-7500T, 4c"), (None, "5.68 GiB memory"), (None, "integrated graphics"),
     (None, "NVMe 238 GiB"), (None, "HDD 465 GiB · unused")])
node("red", "red-server", "192.168.70.13", [("intel", "Core i5-8500T, 6c"), (None, "15.46 GiB memory"), (None, "integrated graphics"),
     (None, "NVMe 238 GiB"), (None, "HDD 931 GiB · media /data")])
node("green", "green-server", "192.168.70.14", [("intel", "Core i5-8500T, 6c"), (None, "15.46 GiB memory"), (None, "integrated graphics"),
     (None, "NVMe 238 GiB"), (None, "!empty storage pool"), (None, "!host memory errors unresolved"), (None, "no guests")])

def guest(node_id, id, name, kind, vlan, ip, logo, icons=()):
    d.card(node_id, id, name, sub1=f"{kind} · VLAN {vlan}", sub2=ip, logo=logo, icons=icons)

guest("grey", "kali", "kali-pen", "VM 102", 40, "stopped", "kali-linux")
guest("grey", "win11", "win11-dev", "VM 103", 40, "192.168.40.117", "windows-11")
guest("grey", "ubuntu", "ubuntu-dev", "VM 105", 40, "192.168.40.179", "ubuntu")
guest("grey", "splunk", "splunk-siem", "VM 109", 72, "192.168.72.3", "splunk", ["rocky-linux"])
guest("grey", "dmain", "docker-main", "LXC 110", 40, "192.168.40.35", "docker", ["immich", "forgejo"])
guest("grey", "sec01", "security-01", "VM 200", 72, "192.168.72.2", "wazuh", ["ubuntu"])
guest("grey", "dc01", "HQ-DC01", "VM 301", 65, "192.168.65.10", "windows-server")
guest("grey", "dc02", "HQ-DC02", "VM 302", 65, "192.168.65.11", "windows-server")
guest("grey", "mgt01", "HQ-MGT01", "VM 303", 65, "192.168.65.12", "windows-server")
guest("grey", "ws001", "HQ-WS001", "VM 310", 65, "192.168.65.20", "windows-11")
guest("purple", "app01", "app-01", "VM 116", 80, "192.168.80.10", "coolify", ["traefik", "debian"])
guest("purple", "edge01", "edge-01", "VM 121", 30, "192.168.30.10", "caddy", ["cloudflared", "debian"])
guest("purple", "alpha", "alpha-prod-01", "VM 401", 80, "192.168.80.118", "teamspeak", ["debian"])
guest("blue", "ansible", "ansible-01", "LXC 100", 40, "192.168.40.36", "ansible", ["semaphore"])
guest("blue", "mon01", "monitor-01", "LXC 104", 73, "192.168.73.2", "grafana", ["prometheus", "peanut"])
guest("blue", "dnet", "docker-network", "LXC 107", 85, "192.168.85.2", "nginx-proxy-manager", ["netbird"])
guest("blue", "dblue", "docker-blue", "LXC 108", 40, "192.168.40.39", "docker", ["rustdesk", "meshcentral"])
guest("red", "media", "media-01", "LXC 842", 40, "192.168.40.42", "jellyfin", ["seerr", "sonarr", "radarr", "gluetun"])

d.group("power", "Power", badge="UPS", family="External")
d.card("power", "ups", "UPS-02", sub1="feeds grey, blue and red", sub2="purple and green not on it", logo="apc")

d.row("grey", "purple", "blue", "red", "green")
d.row("power", stretch=False)
d.bus(0, "Corosync link0 · MGMT-A · VLAN 70", ["grey", "purple", "blue", "red", "green"], color="blue")
d.bus(0, "Corosync link1 · Cluster-Net · VLAN 71", ["grey", "purple", "blue", "red", "green"], color="purple", style="dashed")
d.edge("ups", "grey", "AC power", color="grey", from_side="top", to_side="bottom", label_seg=-1)
d.edge("ups", "blue", "", color="grey", from_side="top", to_side="bottom")
d.edge("ups", "red", "", color="grey", from_side="top", to_side="bottom")

d.legend_family("Mgmt", "Proxmox VE node (AlphaSec-Mgmt)"); d.legend_family("External", "power")
d.legend_edge("Corosync link0", "solid", "blue"); d.legend_edge("Corosync link1", "dashed", "purple"); d.legend_edge("AC power", "solid", "grey")
d.footnote("Guest addresses are the VLAN-side interfaces. win11-dev moved from green to grey on 2026-09-23; green-server carries no guests until its memory errors are resolved.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
