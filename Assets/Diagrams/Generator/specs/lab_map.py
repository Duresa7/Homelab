#!/usr/bin/env python3
"""lab-map: the index at the top of Guides/README.md. The five Galaxy nodes and
every guest as small cards grouped by what they do, each group carrying the
guide that covers it. Guide list: Guides/README.md (2026-09-18). Node and guest
facts: .scratch/reorg/BRIEF.md tables (2026-09-24). Retired platforms
(Portainer, TNIO, Kasm, game-01, debian-dev) are absent by design."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lab-map.svg")
d = Diagram("lab-map", "Lab map: where each guide lands",
            "Five Galaxy nodes and eighteen guests grouped by what they do; the pill on each group names the guide that covers it",
            source="Guides/README.md, Operations/Inventory/Galaxy/VMs.md and LXCs.md, Infrastructure/Hardware/Nodes.md",
            width=1640, card_w=176)

# --- row 0: the edge, remote access and the procedures that apply everywhere ---
d.group("edge", "Edge: from the Internet to the lab", badge="Guide: UniFi Network", family="External",
        notes=[(None, "Cloudflare has no standalone guide yet; the Tunnel ends on edge-01, and no port is forwarded")])
d.card("edge", "cf", "Cloudflare", sub1="DNS for alphasecunited.com", sub2="Tunnel, no port forwards", logo="cloudflare")
d.card("edge", "gw", "Ahsoka Gateway", sub1="UCG-Fiber, UniFi Network 10.6", sub2="16 VLANs, zone-based firewall", logo="unifi")
d.card("edge", "edge01", "edge-01", sub1="Caddy, cloudflared", sub2="DMZ VLAN 30, public ingress", logo="caddy", icons=["cloudflared"], node="purple")
d.group("shared", "Shared procedures", badge="3 guides", family="External", notes=[
    (None, "Linux Host Baseline: each Linux guest before any workload"),
    (None, "SSH Key Lifecycle: three approved keys; audit, rotate, retire"),
    (None, "Security Incident Response: contain, rotate, check, close")])

# --- row 1: the nodes; the workstations now sit in row 3 with the other guests ---
d.group("galaxy", "Compute: Galaxy cluster, Proxmox VE 9.2.11", badge="Guide: Galaxy Proxmox Cluster", family="Mgmt",
        notes=[(None, "MGMT-A, VLAN 70; Corosync second ring on Cluster-Net, VLAN 71")])
d.card("galaxy", "grey", "grey-server", sub1="192.168.70.10", sub2="10 guests, GTX 1080 Ti", logo="proxmox", node="grey")
d.card("galaxy", "purple", "purple-server", sub1="192.168.70.11", sub2="3 guests", logo="proxmox", node="purple")
d.card("galaxy", "blue", "blue-server", sub1="192.168.70.12", sub2="4 guests", logo="proxmox", node="blue")
d.card("galaxy", "red", "red-server", sub1="192.168.70.13", sub2="1 guest, media disk", logo="proxmox", node="red")
d.card("galaxy", "green", "green-server", sub1="192.168.70.14", sub2="no guests, memory errors", logo="proxmox", node="green", warn=True)
d.group("ws", "Workstations", badge="no guide of their own", family="Internal", notes=[(None, "Personal-A, VLAN 40")])
d.card("ws", "ubuntu", "ubuntu-dev", sub1="Ubuntu 26.04.1, Docker", sub2="VS Code, agent tooling", logo="ubuntu", node="grey")
d.card("ws", "win11", "win11-dev", sub1="Windows 11 Pro 25H2", sub2="OpenSSH, dev VM", logo="windows-11", node="grey")
d.card("ws", "kali", "kali-pen", sub1="Kali 2026.2", sub2="pentest VM, stopped", logo="kali-linux", node="grey")

# --- rows 0 to 2: access (row 0), identity, security and monitoring (row 2) --------
d.group("access", "Access", badge="Guides: NetBird, Nginx Proxy Manager", family="Access",
        notes=[(None, "NetBird routes peers to VLAN 85")])
d.card("access", "dnet", "docker-network", sub1="NPM 2.15, NetBird", sub2="Access-A, VLAN 85", logo="nginx-proxy-manager", icons=["netbird"], node="blue")
d.group("identity", "Identity: ad.alphasecunited.com", badge="Guide: Active Directory", family="Identity")
d.card("identity", "dc01", "HQ-DC01", sub1="Windows Server 2025", sub2="domain controller", logo="windows-server", node="grey")
d.card("identity", "dc02", "HQ-DC02", sub1="Windows Server 2025", sub2="second domain controller", logo="windows-server", node="grey")
d.card("identity", "mgt01", "HQ-MGT01", sub1="Windows Admin Center 2.7", sub2="Entra provisioning agent", logo="windows-server", icons=["entra-id"], node="grey")
d.card("identity", "ws001", "HQ-WS001", sub1="Windows 11 Pro 25H2", sub2="domain workstation", logo="windows-11", node="grey")
d.group("secmon", "Security and monitoring", badge="Guides: Wazuh, Wazuh Alerts in Splunk, Splunk, Prometheus", family="Observability")
d.card("secmon", "sec01", "security-01", sub1="Wazuh 4.14.7 manager", sub2="Wazuh MCP, Security-A 72", logo="wazuh", node="grey")
d.card("secmon", "splunk", "splunk-siem", sub1="Splunk 10.4, SC4S", sub2="Enterprise Security", logo="splunk", icons=["rocky-linux"], node="grey")
d.card("secmon", "mon01", "monitor-01", sub1="Prometheus, Grafana", sub2="PeaNUT, MONITOR-A 73", logo="grafana", icons=["prometheus", "peanut"], node="blue")

# --- rows 1 and 3: media, applications (row 3), automation (row 1) --------------------
d.group("media", "Media", badge="Guide: Media Stack", family="Internal", notes=[(None, "Personal-A, VLAN 40")])
d.card("media", "media01", "media-01", sub1="Jellyfin, Seerr, *arr", sub2="qBittorrent via Gluetun", logo="jellyfin", icons=["seerr", "sonarr", "radarr", "gluetun"], node="red")
d.group("apps", "Applications and photos", badge="Guide: Immich Storage Migration", family="Servers",
        notes=[(None, "Coolify, Dockhand 1.0.48, App Portal and TeamSpeak have no guide yet")])
d.card("apps", "dmain", "docker-main", sub1="Immich 3.2, Forgejo 16", sub2="Dockhand, App Portal", logo="immich", icons=["forgejo", "dockhand", "ollama", "booklore"], node="grey")
d.card("apps", "app01", "app-01", sub1="Coolify 4.3.23, Traefik", sub2="SERVERS-A, VLAN 80", logo="coolify", icons=["traefik"], node="purple")
d.card("apps", "alpha", "alpha-prod-01", sub1="TeamSpeak, SERVERS-A", sub2="TS3 Manager, Playit", logo="teamspeak", icons=["playit"], node="purple")
d.group("auto", "Automation and agents", badge="Guide: Ansible SSH Identity Automation", family="Internal",
        notes=[(None, "Executor and the MCP gateways have no guide yet")])
d.card("auto", "ansible", "ansible-01", sub1="Ansible 14.2, Semaphore 2.18", sub2="fleet updates, Galaxy PXE", logo="ansible", icons=["semaphore"], node="blue")
d.card("auto", "dblue", "docker-blue", sub1="Executor 1.6.10, MCP gateways", sub2="RustDesk, MeshCentral", logo="docker", icons=["rustdesk", "meshcentral"], node="blue")

# Access sits with the edge (it is how remote users get in), automation beside the cluster it updates and
# PXE-boots, and the workstations with the other Personal-A guests; each row then has room for its text.
d.row("edge", "access", "shared")
d.row("galaxy", "auto")
d.row("identity", "secmon")
d.row("ws", "media", "apps")

d.edge("gw", "galaxy", "every VLAN reaches the five nodes through Bane Switch POE", color="grey", t_off=-173)  # straight drop from the gateway card

d.legend_family("External", "edge and procedures"); d.legend_family("Mgmt", "Galaxy node"); d.legend_family("Internal", "lab guests")
d.legend_family("Access", "access"); d.legend_family("Identity", "identity"); d.legend_family("Observability", "security and monitoring")
d.legend_family("Servers", "applications")
for n in ("grey", "purple", "blue", "red", "green"): d.legend_badge(f"runs on {n}-server", n)
d.footnote("The stripe on a guest card names the node that runs it. Addresses, IDs and versions are in the Galaxy inventory; this map only says what each host is for and which guide to open.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
