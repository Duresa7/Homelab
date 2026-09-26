#!/usr/bin/env python3
"""netbird: the self-hosted control plane on docker-network, how peers reach it
through Nginx Proxy Manager, the WireGuard mesh, and the routed path into
Access-A (restyle of the 2026-07-20 diagram, content kept, versions updated).
Facts: Platforms/Netbird/README.md (containers, bindings, routing peer),
Platforms/Netbird/Configuration/Access-Network.md (AlphaSec-Galaxy network,
the one granted resource, masquerade, how the gateway sees it), Change Record
First Peer and Routed VPN Path - 2026-07-12 (first peer), Guides/NetBird.md
(versions verified 2026-09-24), Infrastructure/Network/UniFi/Configuration/
firewall.md (the AlphaSec-Access zone allows)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "netbird.svg")
d = Diagram("netbird", "NetBird: self-hosted control plane and the routed path into Access-A",
            "One combined netbird-server and the dashboard on docker-network, published by Nginx Proxy Manager; peers form a WireGuard mesh and reach VLAN 85 through the routing peer",
            source="Platforms/Netbird/README.md, Platforms/Netbird/Configuration/Access-Network.md, Platforms/Netbird/Documentation/Change Records/First Peer and Routed VPN Path - 2026-07-12.md, Guides/NetBird.md, Infrastructure/Network/UniFi/Configuration/firewall.md",
            width=1640, row_gap=64)

# --- row 0: the peers, and what UniFi contributes -----------------------------------------
d.group("peers", "Remote peers", badge="WireGuard mesh", family="External")
d.card("peers", "peer", "NetBird clients", sub1="any network; enrolled with a setup key from the dashboard", sub2="management, signal and relay via the one HTTPS name", logo="netbird", icons=["wireguard"])
d.card("peers", "first", "First peer, 2026-07-12", sub1="Debian 13 client, NetBird 0.74.4 at the time", sub2="overlay 100.121.231.114; proved the route with HTTPS 200", logo="debian")
d.group("unifi", "UniFi", badge="Ahsoka Gateway", family="Internal")
d.card("unifi", "dns", "Local DNS", sub1="netbird.alphasecunited.com answers 192.168.85.2", sub2="LAN only; nothing is in public DNS", logo="unifi")
d.card("unifi", "zone", "Zone firewall, AlphaSec-Access", sub1="policies: Allow Internal to AlphaSec-Access (all),", sub2="Allow VPN to AlphaSec-Access (all); LXC egress: web, NTP", logo="unifi")

# --- row 1: the host ---------------------------------------------------------------------------
d.group("host", "docker-network · LXC 107", badge="192.168.85.2 · Access-A VLAN 85 · blue-server · Debian 13", family="Access")
d.card("host", "dash", "netbird-dashboard v2.93.0", sub1="127.0.0.1:8080 direct · netbird-dashboard:80 on proxy", sub2="image netbirdio/dashboard:latest", logo="netbird", node="blue")
d.card("host", "npm", "Nginx Proxy Manager 2.15.1", sub1="172.31.85.10 on proxy · TCP 80 and 443 on 192.168.85.2", sub2="netbird.alphasecunited.com: wildcard cert, Force SSL", logo="nginx-proxy-manager", node="blue")
d.card("host", "server", "netbird-server 0.79.0, combined", sub1="management, signal, relay and the embedded IdP in one", sub2="127.0.0.1:8081 direct · netbird-server:80 · STUN UDP 3478", logo="netbird", node="blue")
d.card("host", "client", "NetBird client · routing peer", sub1="overlay 100.121.111.204 on wt0 · ip_forward on", sub2="sole router of AlphaSec-Galaxy, masquerade on, metric 9999", logo="netbird", icons=["wireguard", "wazuh"], node="blue")

# --- row 2: what the route reaches, and how the gateway sees it ------------------------------------
d.group("net", "AlphaSec-Galaxy · NetBird network", badge="Networks model · default deny", family="Access")
d.card("net", "names", "24 internal names behind NPM", sub1="all proxied from 192.168.85.2, so the one route covers them", sub2="by address off-LAN; the names resolve only on the LAN", logo="nginx-proxy-manager")
d.card("net", "res", "Resource 192.168.85.0/24", sub1="the one reachable resource of 13 defined", sub2="policy Peers to Access-A: source All, all ports", logo="glyph:85")
d.group("gw", "How the gateway sees routed traffic", family="External", notes=[
    (None, "masquerade rewrites the source to 192.168.85.2, so a remote peer's"),
    (None, "traffic originates inside AlphaSec-Access and follows that zone's"),
    (None, "rules; no separate gateway rule was needed for the VPN path."),
    (None, "Peers install 192.168.85.0/24 into routing table 7120 on wt0.")])
d.card("gw", "wg", "UniFi WireGuard server: Management Access", sub1="10.6.0.1/24 · UDP 51822 · zone Vpn · the other remote path", sub2="Allow VPN to AlphaSec-Access is the zone allow that covers it", logo="wireguard", icons=["unifi"])

d.row("peers", "unifi")
d.row("host")
d.row("gw", "net")

def align(src, dst):
    d._layout(); s, t = d.items[src], d.items[dst]
    return (t.x + t.w / 2) - (s.x + s.w / 2)

# reaching the control plane
d.edge("peer", "npm", "HTTPS 443 · API, OAuth2, signal, management, gRPC routes", color="blue", s_off=-40, y="gap:0:-16", label_seg=1, label_x="mid:npm:-20")
d.edge("peer", "server", "STUN UDP 3478", style="dashed", color="teal", s_off=0, y="gap:0:+2", label_seg=1, label_x="mid:server:-40")
d.edge("peer", "client", "WireGuard mesh, wt0", style="dashed", color="teal", arrows="both", s_off=40, y="gap:0:+20", label_seg=1, label_x="mid:client:-60")
d.edge("npm", "dash", "", color="blue")
d.edge("npm", "server", "", color="blue")
# the routed path
d.edge("client", "res", "routes 192.168.85.0/24 with masquerade", color="teal")

d.legend_family("External", "outside the lab, or a note"); d.legend_family("Internal", "UniFi"); d.legend_family("Access", "AlphaSec-Access, VLAN 85")
d.legend_edge("HTTPS through NPM", "solid", "blue"); d.legend_edge("WireGuard mesh and STUN", "dashed", "teal"); d.legend_edge("routed path into the lab", "solid", "teal")
d.legend_icon("wazuh", "Wazuh agent 011 on the host"); d.legend_badge("runs on blue-server", "blue")
d.footnote("Versions read on 2026-09-24: management server 0.79.0 from the combined netbird-server's startup log, dashboard v2.93.0 from its image label; both images track latest. There is no separate signal, relay or management container.")
d.footnote("NetBird trusts only 172.31.85.10/32 as its HTTP proxy. The overlay DNS domain is netbird.selfhosted with no nameserver groups, so a remote peer reaches NPM by address but cannot resolve the alphasecunited.com names off the LAN.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
