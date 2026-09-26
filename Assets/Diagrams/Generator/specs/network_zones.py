#!/usr/bin/env python3
"""network-zones: the UniFi view. Every VLAN in .scratch/reorg/BRIEF.md with its
zone and purpose, representative members from the guest table, the WAN
uplinks, the ProtonVPN client network, the NetBird remote-user mesh, and the
UniFi devices. Deleted networks are absent by design."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "unifi-network.svg")
d = Diagram("network-zones", "UniFi network: VLANs and firewall zones",
            "UniFi Network 10.6 on Ahsoka Gateway. Sixteen networks in eight zones; the zone-based firewall decides what crosses between them",
            source="Infrastructure/Network/UniFi/README.md and Infrastructure/Network/UniFi/Configuration/", width=1640)

d.group("ext", "Outside the gateway", badge="WAN side", family="External")
d.card("ext", "wan1", "WAN 1", sub1="Verizon ONT", sub2="primary uplink", logo="verizon")
d.card("ext", "wan2", "WAN 2", sub1="configured failover", sub2="no link on 2026-09-24", logo="glyph:WAN")
d.card("ext", "proton", "ProtonVPN client", sub1="VPN client network on the gateway", sub2="egress for Proton-WiFi", logo="proton-vpn")
d.card("ext", "remote", "Remote users", sub1="NetBird WireGuard mesh", sub2="routed path into the lab", logo="netbird")
d.card("ext", "cf", "Cloudflare", sub1="DNS: alphasecunited.com", sub2="Tunnel to edge-01, no port forwards", logo="cloudflare")

d.group("devices", "UniFi devices", badge="Management (untagged) · Zone: Internal", family="Internal")
d.card("devices", "gw", "Ahsoka Gateway", sub1="UCG-Fiber · UniFi Network 10.6", sub2="zone-based firewall, one live uplink", logo="unifi", span=2)
d.card("devices", "sw", "Bane Switch POE", sub1="USW-Pro-Max-16-PoE", sub2="core switch", logo="unifi")
d.card("devices", "sw2", "Two more switches", sub1="downstream of Bane", logo="unifi")
d.card("devices", "ap", "Access point", sub1="one UniFi AP", sub2="wireless networks", logo="unifi")

d.group("internal", "Internal", badge="7 networks", family="Internal")
d.card("internal", "v0", "Management", sub1="UniFi fabric, untagged", sub2="gateway, switches, AP", logo="glyph:0", icons=["unifi"])
d.card("internal", "v5", "Server-Provision", sub1="PXE lane, bare-metal nodes", sub2="Galaxy nodes boot here", logo="glyph:5", icons=["proxmox"])
d.card("internal", "v10", "Trusted", sub1="household personal devices", logo="glyph:10")
d.card("internal", "v40", "Personal-A", sub1="lab and utility guests", sub2="7 guests in 192.168.40.x", logo="glyph:40",
       icons=["ubuntu", "windows-11", "kali-linux", "ansible", "docker", "jellyfin"])
d.card("internal", "v45", "Proton-WiFi", sub1="VPN-egress wireless", sub2="leaves through ProtonVPN", logo="glyph:45", icons=["proton-vpn"])
d.card("internal", "v50", "Secure", sub1="admin workstation", sub2="Jedi PC 192.168.50.241", logo="glyph:50", icons=["glyph:PC"])
d.card("internal", "v60", "Secure Client", sub1="end-user PCs", sub2="ObiPC, domain-joined", logo="glyph:60", icons=["windows-11"])

d.group("untrusted", "Untrusted", family="Untrusted")
d.card("untrusted", "v20", "IoT", sub1="appliances", sub2="no lab members", logo="glyph:20")
d.group("dmz", "Dmz", family="Dmz")
d.card("dmz", "v30", "DMZ", sub1="edge-01 ingress, 192.168.30.10", sub2="Caddy behind the Cloudflare Tunnel", logo="glyph:30", icons=["caddy", "cloudflared"])
d.group("identity", "AlphaSec-Identity", family="Identity")
d.card("identity", "v65", "IDENTITY-A", sub1="AD forest ad.alphasecunited.com", sub2="two DCs, HQ-MGT01, HQ-WS001", logo="glyph:65", icons=["windows-server", "windows-11"])
d.group("access", "AlphaSec-Access", family="Access")
d.card("access", "v85", "Access-A", sub1="docker-network 192.168.85.2", sub2="NPM 2.15, NetBird management", logo="glyph:85", icons=["nginx-proxy-manager", "netbird"])

d.group("mgmt", "AlphaSec-Mgmt", family="Mgmt")
d.card("mgmt", "v70", "MGMT-A", sub1="Proxmox management, Corosync link0", sub2="five nodes 192.168.70.10 to .14", logo="glyph:70", icons=["proxmox"])
d.card("mgmt", "v71", "Cluster-Net", sub1="Corosync link1", sub2="second ring for the five nodes", logo="glyph:71", icons=["proxmox"])
d.group("obs", "AlphaSec-Observability", family="Observability")
d.card("obs", "v72", "Security-A", sub1="security-01 (.2), splunk-siem (.3)", sub2="192.168.72.x · Wazuh manager, Splunk", logo="glyph:72", icons=["wazuh", "splunk"])
d.card("obs", "v73", "MONITOR-A", sub1="monitor-01 192.168.73.2", sub2="Prometheus, Grafana, PeaNUT", logo="glyph:73", icons=["prometheus", "grafana", "peanut"])
d.group("servers", "AlphaSec-Servers", family="Servers")
d.group("policy", "Firewall", badge="Ahsoka Gateway", family="External", notes=[
    (None, "zone-based firewall on the gateway"), (None, "sixteen networks, eight zones"),
    (None, "no inbound port forwards from either WAN"), (None, "Cloudflare Tunnel is the only public path")])
d.card("servers", "v80", "SERVERS-A", sub1="app-01 (.10), alpha-prod-01 (.118)", sub2="192.168.80.x · Coolify, TeamSpeak", logo="glyph:80", icons=["coolify", "traefik", "teamspeak"])

d.row("ext")
d.row("devices")
d.row("internal")
d.row("untrusted", "dmz", "identity", "access", "servers")
d.row("mgmt", "obs", "policy")

d.edge("wan1", "gw", "uplink", t_off=-150)
d.edge("wan2", "gw", "uplink", t_off=-40)
d.edge("gw", "proton", "VPN client network", style="dashed", color="teal", from_side="top", to_side="bottom", s_off=180, y="gap:0:-14", label_seg=1)
d.edge("remote", "gw", "WireGuard mesh, routed", style="dashed", color="teal", t_off=230, y="gap:0", label_seg=1)
d.edge("cf", "gw", "Tunnel, outbound from edge-01", style="dashed", color="blue", t_off=280, y="gap:0:14", label_seg=1)
d.edge("gw", "sw", "", color="grey")
d.edge("sw", "sw2", "", color="grey")

d.legend_family("Internal", "Internal"); d.legend_family("Untrusted", "Untrusted"); d.legend_family("Dmz", "Dmz")
d.legend_family("Identity", "AlphaSec-Identity"); d.legend_family("Access", "AlphaSec-Access"); d.legend_family("Mgmt", "AlphaSec-Mgmt")
d.legend_family("Observability", "AlphaSec-Observability"); d.legend_family("Servers", "AlphaSec-Servers"); d.legend_family("External", "outside the lab")
d.legend_edge("wired path", "solid", "grey"); d.legend_edge("tunnel, VPN or mesh", "dashed", "teal")
d.legend_icon("glyph:40", "VLAN ID; 0 marks the untagged network")
d.footnote("Member addresses come from the guest inventory; the VLAN records hold the subnet definitions. Cloudflare has no inbound port forwards: the only public path is the Tunnel that terminates on edge-01.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
