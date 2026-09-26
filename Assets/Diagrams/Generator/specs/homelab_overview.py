#!/usr/bin/env python3
"""homelab-overview: the hero diagram for the root README.

Every fact is taken from .scratch/reorg/BRIEF.md (2026-09-24): the node,
guest and VLAN tables, the network paragraph and the "Flows worth knowing"
paragraph. Nothing retired is drawn.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from ext_rowgaps import Diagram  # per-row gaps: the AD and NPM pills share gap 3, gap 4 carries nothing

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "homelab-overview.svg")

d = Diagram("homelab-overview", "AlphaSec United homelab",
            "One live WAN uplink, a zone-based UniFi firewall, and the five-node Galaxy Proxmox VE cluster that carries every guest",
            source="Operations/Inventory/Galaxy/ (VMs.md, LXCs.md, Services.md), Infrastructure/Network/UniFi/README.md, Infrastructure/Hardware/Nodes.md",
            width=1640, row_gaps={3: 48, 4: 24})

# --- row 0: the outside world ------------------------------------------------
d.group("ext", "Internet and cloud services", badge="outside the lab", family="External")
d.card("ext", "remote", "Remote peers", sub1="NetBird WireGuard mesh", sub2="routed path into the lab", logo="netbird")
d.card("ext", "wan1", "WAN 1", sub1="Verizon ONT", sub2="primary uplink", logo="verizon")
d.card("ext", "wan2", "WAN 2", sub1="configured failover", sub2="no link on 2026-09-24", logo="glyph:WAN")
d.card("ext", "proton", "Proton VPN", sub1="VPN client network", sub2="Proton-WiFi egress, Gluetun", logo="proton-vpn")
d.card("ext", "cf", "Cloudflare", sub1="DNS: alphasecunited.com", sub2="Tunnel · no port forwards", logo="cloudflare")
d.card("ext", "discord", "Discord", sub1="one alert channel", sub2="Grafana alerts, Discord bot", logo="discord")

# --- row 1: UniFi fabric and the two ingress VLANs ---------------------------
d.group("access", "Access-A", badge="VLAN 85", family="Access")
d.card("access", "dnet", "docker-network", sub1="192.168.85.2 · NPM 2.15", sub2="NetBird mgmt and dashboard", logo="nginx-proxy-manager", icons=["netbird", "wazuh"], node="blue")
d.group("unifi", "UniFi Network 10.6", badge="Zone: Internal · Management (untagged)", family="Internal")
d.card("unifi", "gw", "Ahsoka Gateway", sub1="UCG-Fiber · zone-based firewall", sub2="WAN 1 live, WAN 2 no link, ProtonVPN client", logo="unifi", span=2)
d.card("unifi", "sw", "Bane Switch POE", sub1="USW-Pro-Max-16-PoE", sub2="plus two more switches", logo="unifi")
d.card("unifi", "ap", "Access point", sub1="one UniFi AP", sub2="wireless networks", logo="unifi")
d.group("dmz", "DMZ", badge="VLAN 30", family="Dmz")
d.card("dmz", "edge01", "edge-01", sub1="192.168.30.10 · Debian 13", sub2="Caddy, cloudflared connector", logo="caddy", icons=["cloudflared", "wazuh"], node="purple")

# --- row 2: servers and observability ------------------------------------------
d.group("other", "Other networks", badge="Zones: Internal, Untrusted", family="Internal", notes=[
    (None, "Trusted · VLAN 10 · household personal devices"),
    (None, "IoT · VLAN 20 · appliances (zone Untrusted)"),
    (None, "Server-Provision · VLAN 5 · PXE lane for nodes"),
    (None, "Proton-WiFi · VLAN 45 · VPN-egress wireless"),
])
d.group("servers", "SERVERS-A", badge="VLAN 80", family="Servers")
d.card("servers", "app01", "app-01", sub1="192.168.80.10 · Debian 13", sub2="Coolify 4.3.23, Traefik 3.7.12", logo="coolify", icons=["traefik", "wazuh"], node="purple")
d.card("servers", "alpha", "alpha-prod-01", sub1="192.168.80.118 · Debian 13", sub2="TeamSpeak, TS3 Manager", logo="teamspeak", icons=["playit", "wazuh"], node="purple")
d.group("sec", "Security-A", badge="VLAN 72 · AlphaSec-Observability", family="Observability")
d.card("sec", "sec01", "security-01", sub1="192.168.72.2 · Ubuntu 24.04", sub2="Wazuh 4.14.7 manager", logo="wazuh", icons=["node-exporter", "cadvisor"], node="grey")
d.card("sec", "splunk", "splunk-siem", sub1="192.168.72.3 · Rocky 10.2", sub2="Splunk 10.4, SC4S syslog", logo="splunk", icons=["rocky-linux"], node="grey")
d.group("mon", "MONITOR-A", badge="VLAN 73", family="Observability")
d.card("mon", "mon01", "monitor-01", sub1="192.168.73.2 · LXC", sub2="Prometheus and Grafana", logo="grafana", icons=["prometheus", "peanut", "wazuh"], node="blue")

# --- row 3: identity and the physical workstations --------------------------
d.group("identity", "IDENTITY-A · ad.alphasecunited.com", badge="VLAN 65 · AlphaSec-Identity", family="Identity")
d.card("identity", "dc01", "HQ-DC01", sub1="192.168.65.10 · WS 2025", sub2="domain controller", logo="windows-server", node="grey")
d.card("identity", "dc02", "HQ-DC02", sub1="192.168.65.11 · WS 2025", sub2="second domain controller", logo="windows-server", node="grey")
d.card("identity", "mgt01", "HQ-MGT01", sub1="192.168.65.12 · WS 2025", sub2="WAC 2.7, Entra provisioning", logo="windows-server", icons=["entra-id"], node="grey")
d.card("identity", "ws001", "HQ-WS001", sub1="192.168.65.20 · Win 11 Pro", sub2="domain workstation", logo="windows-11", node="grey")
d.group("secure_client", "Secure Client", badge="VLAN 60", family="Internal")
d.card("secure_client", "obipc", "ObiPC", sub1="physical PC, domain-joined", sub2="Action1, Intune, AppLocker", logo="windows-11", icons=["microsoft-intune"])
d.group("secure", "Secure", badge="VLAN 50", family="Internal")
d.card("secure", "jedi", "Jedi PC", sub1="192.168.50.241", sub2="privileged workstation", logo="glyph:PC")

# --- row 4: lab and utility guests ------------------------------------------------
d.group("personal", "Personal-A", badge="VLAN 40 · Internal", family="Internal")
d.card("personal", "ubuntu", "ubuntu-dev", sub1="192.168.40.179 · Docker", sub2="Ubuntu 26.04.1, VS Code", logo="ubuntu", icons=["node-exporter", "wazuh"], node="grey")
d.card("personal", "win11", "win11-dev", sub1="192.168.40.117 · OpenSSH", sub2="Windows 11 Pro 25H2 dev", logo="windows-11", node="grey")
d.card("personal", "kali", "kali-pen", sub1="stopped · Kali 2026.2", sub2="pentest VM", logo="kali-linux", icons=[], node="grey")
d.card("personal", "ansible", "ansible-01", sub1="192.168.40.36 · Ansible 14.2", sub2="Semaphore 2.18, PXE", logo="ansible", icons=["semaphore", "wazuh"], node="blue")
d.card("personal", "dblue", "docker-blue", sub1="192.168.40.39 · LXC", sub2="Executor and MCP gateways", logo="docker", icons=["rustdesk", "meshcentral", "wazuh"], node="blue")
d.card("personal", "dmain", "docker-main", sub1="192.168.40.35 · Immich 3.2", sub2="Forgejo 16, Dockhand 1.0.48", logo="docker", icons=["forgejo", "ollama", "open-webui", "booklore", "dockhand", "wazuh"], node="grey")
d.card("personal", "media", "media-01", sub1="192.168.40.42 · Jellyfin", sub2="Seerr, *arr, qBittorrent", logo="jellyfin", icons=["seerr", "sonarr", "radarr", "gluetun", "wazuh"], node="red")

# --- row 5: the compute substrate ----------------------------------------------------
d.group("galaxy", "Galaxy cluster · Proxmox VE 9.2.11", badge="MGMT-A VLAN 70 · Cluster-Net VLAN 71 · AlphaSec-Mgmt", family="Mgmt")
d.card("galaxy", "grey", "grey-server", sub1="192.168.70.10 · Ryzen 7 3700X 8c/16t", sub2="62.72 GiB · GTX 1080 Ti · 3 pools", logo="proxmox", icons=["amd", "nvidia"], node="grey")
d.card("galaxy", "purple", "purple-server", sub1="192.168.70.11 · i5-8500T 6c", sub2="15.46 GiB · NVMe, SSD", logo="proxmox", icons=["intel"], node="purple")
d.card("galaxy", "blue", "blue-server", sub1="192.168.70.12 · i5-7500T 4c", sub2="5.68 GiB · NVMe", logo="proxmox", icons=["intel"], node="blue")
d.card("galaxy", "red", "red-server", sub1="192.168.70.13 · i5-8500T 6c", sub2="15.46 GiB · NVMe, HDD (media)", logo="proxmox", icons=["intel"], node="red")
d.card("galaxy", "green", "green-server", sub1="192.168.70.14 · i5-8500T 6c", sub2="15.46 GiB · empty pool, memory errors", logo="proxmox", icons=["intel"], node="green", warn=True)

d.row("ext")
d.row("access", "unifi", "dmz")
d.row("other", "servers", "sec", "mon")
d.row("identity", "secure_client", "secure")
d.row("personal")
d.row("galaxy")

# --- flows ------------------------------------------------------------------------
d.edge("wan1", "gw", "uplink", color="grey", t_off=-60)
d.edge("wan2", "gw", "uplink", color="grey", t_off=-20)
d.edge("gw", "proton", "VPN client network", style="dashed", color="teal", from_side="top", to_side="bottom", s_off=60, y="gap:0:14", label_seg=1)
d.edge("cf", "edge01", "Cloudflare Tunnel (outbound)", style="dashed", color="blue", label_seg=1, y="gap:0:-14")
d.edge("remote", "dnet", "NetBird mesh, WireGuard", style="dashed", color="teal")
d.edge("edge01", "app01", "Caddy to Traefik, HTTPS", color="blue", y="gap:1:12", label_seg=1, label_x="mid:app01:+200")
d.edge("gw", "splunk", "CEF syslog 1514", color="orange", y="gap:1:-12", s_off=40, label_seg=1, label_x="mid:splunk:-220")
d.edge("sec01", "splunk", "Wazuh alerts, UF 9997", color="orange", from_side="bottom", to_side="bottom", y="gap:2:-10", s_off=-40, label_seg=1)
d.edge("mon01", "sec01", "Prometheus scrape (node_exporter, cAdvisor)", color="green", from_side="bottom", to_side="bottom", y="gap:2:10", t_off=40, label_seg=1, label_x="mid:mon01:-60")
d.edge("mon01", "discord", "alerts", color="green", from_side="right", to_side="right", x="right", label_x="right:-8", label_y="gap:0", label_anchor="end")
d.edge("dc01", "obipc", "AD domain: ad.alphasecunited.com", color="purple", from_side="bottom", to_side="bottom", y="gap:3:-12", label_seg=1)
# NPM publishes the internal names of the proxied hosts; the edge ends on the Personal-A frame itself,
# entering its header from above, with the pill on the horizontal run through gap 3.
d.edge("dnet", "personal", "internal HTTPS names under alphasecunited.com, DNS-01 cert", color="blue", from_side="left", to_side="top", x="left", y="gap:3:+12", t_off=-360, label_seg=2, label_x="left:+8", label_anchor="start")

d.legend_family("Internal", "Internal"); d.legend_family("Dmz", "Dmz"); d.legend_family("Access", "AlphaSec-Access")
d.legend_family("Servers", "AlphaSec-Servers"); d.legend_family("Observability", "AlphaSec-Observability")
d.legend_family("Identity", "AlphaSec-Identity"); d.legend_family("Mgmt", "AlphaSec-Mgmt"); d.legend_family("External", "outside the lab")
d.legend_edge("traffic or telemetry", "solid", "grey"); d.legend_edge("tunnel, VPN or mesh", "dashed", "teal")
d.legend_icon("wazuh", "Wazuh agent: the five nodes and ten Linux guests report to security-01")
for n in ("grey", "purple", "blue", "red", "green"): d.legend_badge(f"{n}-server", n)
d.footnote("Prometheus on monitor-01 scrapes 57 targets across seven jobs. Dockhand manages containers through Hawser Edge agents. Ansible and Semaphore on ansible-01 run fleet updates.")

d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
