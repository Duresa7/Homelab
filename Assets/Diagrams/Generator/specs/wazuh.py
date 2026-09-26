#!/usr/bin/env python3
"""wazuh: the manager on security-01, the fifteen remote agents by group, the
forwarder path into Splunk, the MCP path from Executor, and the alert path.
Facts: Platforms/Wazuh/README.md and Configuration/README.md (agent IDs, groups,
versions), Platforms/Wazuh/Configuration/Agent Groups/*.conf (what each group
watches), Guides/Wazuh.md (15 active remote agents, 2026-09-18),
Guides/Wazuh-Alerts-in-Splunk.md (UF on 9997), Platforms/Executor/README.md."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "wazuh.svg")
d = Diagram("wazuh", "Wazuh: manager, agent groups and where the alerts go",
            "Fifteen Linux agents report to security-01 on TCP 1514; the alert stream is forwarded to Splunk on 9997, and Executor reads the manager over MCP",
            source="Platforms/Wazuh/README.md, Platforms/Wazuh/Configuration/README.md and Agent Groups/, Guides/Wazuh.md, Guides/Wazuh-Alerts-in-Splunk.md, Platforms/Executor/README.md",
            width=1640, card_w=200)

def agent(group, id, name, ip, aid, node, ver="4.14.6-1, held", extra=None, icons=()):
    d.card(group, id, name, sub1=f"{ip} · ID {aid}", sub2=extra or f"agent {ver}", logo="wazuh", node=node, icons=icons)

# --- row 0: the three groups with their own watches --------------------------------
d.group("proxmox", "proxmox group · the five nodes", badge="IDs 013 to 017", family="Mgmt", notes=[
    (None, "adds no watches: ignores the pmxcfs state files under /etc/pve and keeps its configuration files watched")])
agent("proxmox", "grey", "grey-server", "192.168.70.10", "013", "grey")
agent("proxmox", "purple", "purple-server", "192.168.70.11", "014", "purple")
agent("proxmox", "blue", "blue-server", "192.168.70.12", "015", "blue")
agent("proxmox", "red", "red-server", "192.168.70.13", "016", "red")
agent("proxmox", "green", "green-server", "192.168.70.14", "017", "green")
d.group("edge", "edge group", badge="ID 005", family="Dmz", notes=[
    (None, "adds /etc/cloudflared, /etc/caddy,"), (None, "/tmp, /usr/local/bin, systemd units")])
agent("edge", "edge01", "edge-01", "192.168.30.10", "005", "purple", extra="agent 4.14.5-1, held", icons=["caddy", "cloudflared"])
d.group("workstation", "workstation group", badge="ID 020", family="Internal", notes=[
    (None, "adds Downloads, /opt, /usr/local/bin,"), (None, "payload-shaped files in /tmp")])
agent("workstation", "ubuntu", "ubuntu-dev", "192.168.40.179", "020", "grey", extra="agent 4.14.6-1", icons=["ubuntu"])

# --- row 1: the manager host, Splunk and the alert bot ---------------------------------
d.group("sec01", "security-01 · 192.168.72.2 · VM 200 on grey-server · Ubuntu 24.04", badge="Security-A · VLAN 72", family="Observability", cols=3)
d.card("sec01", "mgr", "Wazuh manager 4.14.7", sub1="1514 events · 1515 enrolment", sub2="15 remote agents, all active", logo="wazuh")
d.card("sec01", "idx", "Indexer and dashboard", sub1="HTTPS 443 · API 55000", sub2="wazuh.alphasecunited.com, NPM", logo="wazuh", icons=["nginx-proxy-manager"])
d.card("sec01", "malware", "Malware detection, twice", sub1="VirusTotal on new file hashes", sub2="rule 100200, known-bad list", logo="virustotal")
d.card("sec01", "mcp", "Wazuh MCP Server 4.3.0", sub1=":3000 · read-only bearer", sub2="41 tools, no active response", logo="wazuh")
d.card("sec01", "uf", "Splunk forwarder 10.4.0", sub1="tails alerts.json", sub2="as splunkfwd in group wazuh", logo="splunk")
d.group("siem", "splunk-siem", badge="192.168.72.3 · Rocky 10.2", family="Observability")
d.card("siem", "splunk", "Splunk Enterprise 10.4", sub1="receiver :9997 · index wazuh", sub2="30 days or 5 GB, wazuh_insights", logo="splunk", icons=["rocky-linux"])
d.group("alerts", "Alerting", badge="monitor-01 · 192.168.73.2", family="Observability")
d.card("alerts", "bot", "Discord alert bot", sub1=":8080/splunk, splunk-siem only", sub2="posts to one Discord channel", logo="discord")

# --- row 2: the agents that carry only the default policy --------------------------------
d.group("default", "default group only · eight guests", badge="every agent is in default", family="Internal", cols=4, notes=[
    (None, "default: real-time watches on /etc/ssh and /etc/cron.d on every agent, rootcheck's trojan check off fleet-wide")])
agent("default", "app01", "app-01", "192.168.80.10", "004", "purple", icons=["coolify"])
agent("default", "alpha", "alpha-prod-01", "192.168.80.118", "006", "purple", icons=["teamspeak"])
agent("default", "dblue", "docker-blue", "192.168.40.39", "007", "blue", extra="Executor 1.6.10 lives here", icons=["docker"])
agent("default", "media", "media-01", "192.168.40.42", "008", "red", icons=["jellyfin"])
agent("default", "ansible", "ansible-01", "192.168.40.36", "009", "blue", icons=["ansible"])
agent("default", "mon01", "monitor-01", "192.168.73.2", "010", "blue", icons=["grafana"])
agent("default", "dnet", "docker-network", "192.168.85.2", "011", "blue", icons=["nginx-proxy-manager"])
agent("default", "dmain", "docker-main", "192.168.40.35", "021", "grey", icons=["docker"])

d.row("proxmox", "edge", "workstation")
d.row("sec01", "siem", "alerts")
d.row("default")

def align(src, dst):
    d._layout(); s, t = d.items[src], d.items[dst]
    return (t.x + t.w / 2) - (s.x + s.w / 2)

# agents to the manager
d.edge("proxmox", "mgr", "TCP 1514 events, 1515 enrolment", color="orange", from_side="bottom", to_side="top", s_off=align("proxmox", "mgr"))
d.edge("edge", "mgr", "TCP 1514", color="orange", from_side="bottom", to_side="top", t_off=24, y="gap:0:-10", label_seg=1)
d.edge("workstation", "mgr", "TCP 1514", color="orange", from_side="bottom", to_side="top", t_off=48, y="gap:0:+10", label_seg=1)
d.edge("default", "sec01", "TCP 1514 · eight agents", color="orange", from_side="top", to_side="bottom", s_off=align("default", "sec01"), label_y="gap:1:+18")
# Executor on docker-blue reads the manager through the MCP server
d.edge("dblue", "mcp", "Executor, MCP over HTTP, read-only bearer", color="blue", from_side="top", to_side="bottom", y="gap:1:-4", label_seg=1, label_x="between:mgr,idx")
# the alert stream
d.edge("uf", "splunk", "TCP 9997 · index wazuh", color="orange", from_side="bottom", to_side="bottom", y="gap:1:-18", t_off=-30)
d.edge("splunk", "bot", "four Wazuh searches, webhook", color="green", from_side="bottom", to_side="bottom", y="gap:1:-18", s_off=30)

d.legend_family("Mgmt", "Proxmox node"); d.legend_family("Dmz", "DMZ"); d.legend_family("Internal", "Personal-A and the other guest VLANs")
d.legend_family("Observability", "AlphaSec-Observability")
d.legend_edge("agent events and alert forwarding", "solid", "orange"); d.legend_edge("MCP, read-only", "solid", "blue"); d.legend_edge("alerts to Discord", "solid", "green")
d.legend_icon("virustotal", "VirusTotal lookup on a file-integrity event")
for n in ("grey", "purple", "blue", "red", "green"): d.legend_badge(f"runs on {n}-server", n)
d.footnote("UniFi object Wazuh Ports admits only TCP 1514 and 1515 to security-01; the API and agent ports are not published through NPM and nothing is exposed to the WAN.")
d.footnote("Fifteen remote agents plus the manager's own agent 000; splunk-siem runs no agent. The manager caps every agent version, so the fleet holds 4.14.6-1 and edge-01 holds 4.14.5-1. Wazuh itself notifies nobody: Splunk's four Wazuh searches are the one emitter.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
