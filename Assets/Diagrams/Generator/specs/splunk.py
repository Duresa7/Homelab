#!/usr/bin/env python3
"""splunk: the SIEM VM, its three inputs, the two apps I wrote, the bounded
indexes and the alert path (restyle of the 2026-08-04 diagram, content kept and
extended to the inputs added since). Facts: Platforms/Splunk/README.md (SC4S,
flow collector, unifi_insights), Enterprise/Documentation/Build Log.md (ports,
indexes, SC4S decision), Change Records 2026-08-28 (netfw, collector), 2026-08-29
(root expansion, wazuh_insights) and 2026-09-03 (nine Discord searches),
Guides/Splunk.md (versions verified 2026-09-24), Guides/Wazuh-Alerts-in-Splunk.md."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "splunk.svg")
d = Diagram("splunk", "Splunk Enterprise and Enterprise Security on splunk-siem",
            "UniFi CEF through SC4S into netops, controller flows through HEC into netfw, Wazuh alerts on 9997 into wazuh; nine saved searches post to Discord through the alert bot",
            source="Platforms/Splunk/README.md, Platforms/Splunk/Enterprise/Documentation/Build Log.md and Change Records/, Guides/Splunk.md, Guides/Wazuh-Alerts-in-Splunk.md",
            width=1640, card_w=200)

# --- row 0: where the data comes from, and who reads or receives from Splunk ---------
d.group("unifi", "UniFi", badge="Ahsoka Gateway · UniFi Network 10.6", family="Internal")
d.card("unifi", "gw", "UniFi console", sub1="System Logging / SIEM export, CEF", sub2="Network, UniFi OS, Protect", logo="unifi")
d.card("unifi", "flows", "Traffic Flows API", sub1="the controller's private v2 API", sub2="per-connection records, risk, policy", logo="unifi")
d.group("sec", "Security-A", badge="VLAN 72", family="Observability")
d.card("sec", "uf", "security-01 · Wazuh manager", sub1="192.168.72.2 · Universal Forwarder 10.4.0", sub2="tails alerts.json as splunkfwd, useACK on", logo="wazuh", icons=["splunk"], node="grey")
d.group("npm", "Access-A", badge="VLAN 85", family="Access")
d.card("npm", "npmc", "Nginx Proxy Manager", sub1="splunk.alphasecunited.com", sub2="the only published port is Splunk Web", logo="nginx-proxy-manager", node="blue")
d.group("mon", "MONITOR-A", badge="VLAN 73", family="Observability")
d.card("mon", "bot", "Discord alert bot", sub1="monitor-01 :8080/splunk", sub2="accepts 192.168.72.3 only; one channel", logo="discord", node="blue")

# --- row 1: the VM ---------------------------------------------------------------------
d.group("vm", "splunk-siem · VM 109", badge="grey-server · Rocky Linux 10.2 · 192.168.72.3 · VLAN 72 · 6 vCPU · 12 GiB · 150 GiB", family="Observability", flow="row")
d.group("inputs", "Inputs", family="Observability")
d.card("inputs", "sc4s", "SC4S 3.45.0", sub1="Podman, container3:latest, systemd", sub2="CEF on TCP and UDP 1514", logo="splunk", icons=["podman"], node="grey")
d.card("inputs", "collector", "unifi-flow-collector.service", sub1="polls every 120 s, 300 s lookback", sub2="unifi_flow_collector.py", logo="glyph:PY", node="grey")
d.group("core", "Splunk Enterprise 10.4.0 · 65 apps", family="Observability")
d.card("core", "es", "Enterprise Security 8.5.1", sub1="loaded once the VM had 6 vCPU", sub2="notables in Incident Review", logo="splunk", node="grey")
d.card("core", "splunk", "Indexer and search head", sub1="HEC 8088 · splunktcp 9997", sub2="Web 8000 · mgmt 8089", logo="splunk", node="grey")
d.card("core", "ui", "unifi_insights", sub1="CIM for six ES data models", sub2="3 dashboards, 8 searches", logo="unifi", node="grey")
d.card("core", "wi", "wazuh_insights", sub1="splunktcp 9997, index wazuh", sub2="CIM, dashboard, 4 searches", logo="wazuh", node="grey")
d.nest("vm", "inputs", "core")

# --- row 2: the indexes ------------------------------------------------------------------
d.group("idx", "Indexes", badge="on the 142 GB root, expanded 2026-08-29", family="Mgmt")
d.card("idx", "netops", "netops", sub1="UniFi CEF events from SC4S", sub2="5 GB cap", logo="glyph:IX")
d.card("idx", "netfw", "netfw", sub1="flow records from the collector", sub2="10240 MB or 180 days", logo="glyph:IX")
d.card("idx", "netx", "netauth, netdns, netids", sub1="created for SC4S routing", sub2="5 GB caps", logo="glyph:IX")
d.card("idx", "wazuh", "wazuh", sub1="sourcetype wazuh:alerts", sub2="30 days or 5 GB", logo="glyph:IX")
d.card("idx", "internal", "_internal, _audit, _introspection", sub1="Splunk's own logs, 22.1 GB", sub2="the biggest thing on the disk", logo="glyph:IX")

d.row("unifi", "sec", "npm", "mon")
d.row("vm")
d.row("idx")

def align(src, dst):
    d._layout(); s, t = d.items[src], d.items[dst]
    return (t.x + t.w / 2) - (s.x + s.w / 2)

# inputs
d.edge("gw", "sc4s", "CEF syslog · TCP and UDP 1514", color="orange", t_off=align("gw", "sc4s"))
d.edge("flows", "collector", "v2 API, polled by the collector", color="orange", t_off=align("flows", "collector"))
d.edge("uf", "splunk", "TCP 9997 · useACK", color="orange", t_off=-30, y="gap:0:-10", label_x="mid:uf:+90", label_y="gap:0:-10")
d.edge("npmc", "splunk", "HTTPS 8000 · Splunk Web", color="blue", t_off=30, y="gap:0:+10", label_x="mid:npmc:-100", label_y="gap:0:+10")
# the alert path: nine searches in the two apps post to the bot
d.edge("core", "bot", "nine saved searches, webhook (5 UniFi, 4 Wazuh)", color="green", from_side="right", to_side="right", x="right",
       label_x="right:-8", label_anchor="end", label_y="gap:0")
# what lands where
d.edge("sc4s", "netops", "HEC 8088, routed by SC4S", color="orange", s_off=align("sc4s", "netops"))
d.edge("collector", "netfw", "HEC 8088", color="orange", s_off=align("collector", "netfw"))
d.edge("splunk", "wazuh", "index wazuh", color="orange", s_off=align("splunk", "wazuh"))

d.legend_family("Internal", "UniFi"); d.legend_family("Observability", "AlphaSec-Observability"); d.legend_family("Access", "AlphaSec-Access"); d.legend_family("Mgmt", "indexes on disk")
d.legend_edge("events and flows into Splunk", "solid", "orange"); d.legend_edge("HTTPS through NPM", "solid", "blue"); d.legend_edge("alerts to Discord", "solid", "green")
d.legend_badge("runs on grey-server", "grey"); d.legend_badge("runs on blue-server", "blue")
d.footnote("Grafana carries states, Splunk carries events: UniFi and Wazuh themselves notify nobody. Eight UniFi correlation searches write notables into Incident Review; the nine Discord-bound searches (five UniFi, four Wazuh) run with digest mode off, so each result row posts once.")
d.footnote("SC4S rather than a Universal Forwarder because UniFi is a closed appliance. The forwarder on security-01 is the only splunktcp source the records show; no Windows host sends to Splunk. UniFi resolves splunk.alphasecunited.com only on the LAN, and HEC, 1514, 8089 and 9997 stay direct.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
