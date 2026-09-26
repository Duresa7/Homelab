#!/usr/bin/env python3
"""prometheus: the monitoring stack on monitor-01, the seven scrape jobs with
their target counts, the exporters on the hosts, and the alert path to Discord.
Facts: Platforms/Prometheus/README.md (57 targets verified 2026-09-16),
Platforms/Prometheus/Configuration/prometheus-config/prometheus.yml (job list),
Guides/Prometheus.md (job counts re-verified 2026-09-24, Grafana 13.2.2),
Platforms/Discord Alert Bot/README.md, Platforms/PeaNUT/README.md."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "prometheus.svg")
d = Diagram("prometheus", "Prometheus and Grafana on monitor-01",
            "Seven scrape jobs, 57 targets, all UP; Grafana's 24 alert rules reach one Discord channel through the alert bot",
            source="Platforms/Prometheus/README.md, Platforms/Prometheus/Configuration/prometheus-config/prometheus.yml, Platforms/Discord Alert Bot/README.md, Platforms/PeaNUT/README.md",
            width=1640, card_w=200)

# --- row 0: what gets scraped ------------------------------------------------------
d.group("names", "Published names", badge="VLAN 85", family="Access")
d.card("names", "npm", "22 HTTPS names", sub1="NPM on docker-network", sub2="and the bot's /health", logo="nginx-proxy-manager")
d.group("nodes", "Galaxy nodes", badge="MGMT-A · VLAN 70", family="Mgmt")
d.card("nodes", "pveapi", "Proxmox VE API", sub1="grey-server :8006", sub2="nodes, guests, storages", logo="proxmox")
d.card("nodes", "nutsrv", "NUT :3493", sub1="grey-server, UPS-02", sub2="UPS-01 not monitored", logo="apc")
d.card("nodes", "ne_nodes", "node_exporter :9100", sub1="1.9.0 on all five nodes", sub2="job node, 5 targets", logo="node-exporter", icons=["proxmox"])
d.group("guests", "Linux guests", badge="12 hosts", family="Internal")
d.card("guests", "ne_guests", "node_exporter :9100", sub1="12 guests, 1.9.0 on most", sub2="1.10.2 on ubuntu-dev", logo="node-exporter", icons=["debian", "ubuntu", "rocky-linux"])
d.card("guests", "cadv", "cAdvisor 0.60.5 :9101", sub1="8 Docker hosts", sub2="CPU, memory, restarts", logo="cadvisor", icons=["docker"])
d.card("guests", "wud", "WUD :9102", sub1="6 Compose hosts, 9.1.0", sub2="update flags, every 5 m", logo="wud", icons=["docker"])

# --- row 1: monitor-01 ------------------------------------------------------------------
d.group("mon", "monitor-01 · 192.168.73.2 · LXC 104 on blue-server", badge="MONITOR-A · VLAN 73", family="Observability")
d.card("mon", "bb", "blackbox_exporter", sub1=":9115 · 23 probes, 60 s", sub2="http_2xx per site root", logo="prometheus")
d.card("mon", "pve", "pve-exporter :9221", sub1="job proxmox · 1 target", sub2="reads grey's PVE API", logo="proxmox")
d.card("mon", "nut", "nut-exporter :9995", sub1="job nut · 1 target", sub2="reads NUT on grey, 30 s", logo="nut")
d.card("mon", "prom", "Prometheus 3.14.0", sub1=":9090 · 57 targets, 7 jobs", sub2="15 s scrape, 15 d kept", logo="prometheus")
d.card("mon", "grafana", "Grafana 13.2.2", sub1=":3000 · 27 dashboards", sub2="24 alert rules, 6 groups", logo="grafana")
d.card("mon", "bot", "Discord alert bot", sub1="webhook :8080", sub2="/grafana and /splunk", logo="discord")
d.card("mon", "peanut", "PeaNUT 6.0.0", sub1=":8090 · UPS dashboard", sub2="same NUT endpoint, UPS-02", logo="peanut")

# --- row 2: who else talks to the bot, and where the exporters come from ---------------
d.group("siem", "Security-A", badge="VLAN 72", family="Observability")
d.card("siem", "splunk", "splunk-siem", sub1="Splunk 10.4.0 · 192.168.72.3", sub2="nine searches, webhook", logo="splunk", icons=["rocky-linux"])
d.group("rollout", "Rollout", badge="ansible-01", family="External", notes=[
    (None, "node_exporter and cAdvisor are deployed by the monitoring-exporters Ansible project on ansible-01"),
    (None, "monitoring images follow :latest except the alert bot; all 27 dashboards and the 24 rules are provisioned from git")])
d.group("ext", "Outside the lab", family="External")
d.card("ext", "discord", "Discord", sub1="one alert channel", sub2="states from Grafana, events from Splunk", logo="discord")

d.row("names", "nodes", "guests")
d.row("mon")
d.row("siem", "rollout", "ext")

def align(src, dst):
    """s_off that makes a vertical edge from src to dst a single straight line."""
    d._layout(); s, t = d.items[src], d.items[dst]
    return (t.x + t.w / 2) - (s.x + s.w / 2)

# scrapes: the scraper pulls, so the arrow leaves the scraper and lands on what it reads
d.edge("bb", "npm", "blackbox · 23 targets", color="green", s_off=align("bb", "npm"), label_seg=-1)
d.edge("pve", "pveapi", "proxmox · 1 target", color="green", s_off=align("pve", "pveapi"), label_seg=-1)
d.edge("nut", "nutsrv", "nut · 1 target", color="green", s_off=align("nut", "nutsrv"), label_seg=-1)
d.edge("prom", "ne_nodes", "node · 5 targets", color="green", s_off=align("prom", "ne_nodes"), label_seg=-1)
d.edge("prom", "ne_guests", "node · 12 targets", color="green", s_off=20, label_seg=-1)
d.edge("prom", "cadv", "cadvisor · 8 targets", color="green", s_off=40, label_seg=-1)
d.edge("prom", "wud", "wud · 6 targets", color="green", s_off=60, label_seg=-1)
# alerts
d.edge("grafana", "bot", "24 rules, one contact point, webhook", color="green", from_side="bottom", to_side="bottom", y="gap:1:-14", t_off=-30)
d.edge("splunk", "bot", "nine saved searches post to /splunk", color="green", from_side="top", to_side="bottom", y="gap:1:+14", t_off=30, label_seg=1)
d.edge("bot", "discord", "one channel", color="green", from_side="bottom", to_side="top", s_off=60, y="gap:1:+14", label_seg=1)

d.legend_family("Access", "AlphaSec-Access"); d.legend_family("Mgmt", "AlphaSec-Mgmt"); d.legend_family("Internal", "Personal-A and the other guest VLANs")
d.legend_family("Observability", "AlphaSec-Observability"); d.legend_family("External", "outside the lab, or a note")
d.legend_edge("scrape or probe, arrow toward what is read", "solid", "green")
d.footnote("One Compose project on monitor-01 runs prometheus, grafana, pve-exporter, blackbox-exporter, nut-exporter and the alert bot; cadvisor, wud, peanut and the Hawser agent run beside it.")
d.footnote("The node job holds 17 targets: the five nodes and twelve guests. Prometheus itself carries no alert rules and there is no Alertmanager; Grafana evaluates the 24 rules and posts through the bot. Grafana carries states, Splunk carries events.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
