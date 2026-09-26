#!/usr/bin/env python3
"""nginx-proxy-manager: the internal HTTPS front door, its certificate path, the
UniFi DNS and firewall that make it work, and the 24 live proxy hosts by
destination (restyle of the 2026-07-20 diagram, content kept and widened from
the NetBird host to all 24). Facts: Platforms/Nginx Proxy Manager/README.md
(2.15.1, pinned, certificate 1, 24 live hosts, 13 policies), Configuration/
internal-proxy-hosts.md (every host and upstream, read 2026-09-24),
Guides/Nginx-Proxy-Manager.md, Infrastructure/Network/UniFi/Configuration/
firewall.md (the Allow NPM to <host> policies) and local-dns.md."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "nginx-proxy-manager.svg")
d = Diagram("nginx-proxy-manager", "Nginx Proxy Manager: internal HTTPS for 24 names",
            "One Let's Encrypt wildcard over a Cloudflare DNS-01 challenge; UniFi local DNS answers every name with 192.168.85.2 and the zone firewall admits NPM to each backend's ports",
            source="Platforms/Nginx Proxy Manager/README.md, Platforms/Nginx Proxy Manager/Configuration/internal-proxy-hosts.md, Guides/Nginx-Proxy-Manager.md, Infrastructure/Network/UniFi/Configuration/firewall.md and local-dns.md",
            width=1640, row_gap=64)

# --- row 0: the client, UniFi, and the certificate path -------------------------------------
d.group("lan", "Clients on the LAN", family="External")
d.card("lan", "client", "Browser or app", sub1="UniFi answers the name, TLS to 192.168.85.2:443", sub2="port 80 redirects to HTTPS; SNI picks the proxy host", logo="glyph:WEB")
d.group("unifi", "UniFi", badge="Ahsoka Gateway", family="Internal")
d.card("unifi", "dns", "Local DNS", sub1="24 A records, one per live host", sub2="all 192.168.85.2; none in public DNS", logo="unifi")
d.card("unifi", "fw", "Zone firewall", sub1="ten Allow NPM to <host> policies", sub2="three more admit hosts to NPM 443", logo="unifi")
d.group("certpath", "Certificate path", family="External")
d.card("certpath", "cf", "Cloudflare", sub1="DNS-01 with a zone-scoped token", sub2="a TXT record, removed after", logo="cloudflare")
d.card("certpath", "le", "Let's Encrypt", sub1="*.alphasecunited.com and apex", sub2="expires 2026-12-08, hourly check", logo="letsencrypt")

# --- row 1: the host ---------------------------------------------------------------------------------
d.group("host", "docker-network · LXC 107", badge="192.168.85.2 · Access-A VLAN 85 · blue-server · Debian 13", family="Access")
d.card("host", "admin", "Admin UI on :81", sub1="http://192.168.85.2:81, no domain name", sub2="33 proxy_host rows: 24 live, 9 soft-deleted", logo="nginx-proxy-manager", node="blue")
d.card("host", "npm", "Nginx Proxy Manager 2.15.1", sub1="TCP 80, 81, 443 on the guest · 172.31.85.10 on proxy", sub2="pinned by tag, out of Dockhand's updates since 2026-09-25", logo="nginx-proxy-manager", node="blue")
d.card("host", "cert1", "Certificate 1, shared by every host", sub1="Force SSL, HTTP/2, Block Common Exploits, WebSockets", sub2="HSTS off; /etc/letsencrypt/live/npm-1/fullchain.pem", logo="letsencrypt", node="blue")
d.card("host", "nb", "netbird.alphasecunited.com", sub1="proxy host 1: netbird-dashboard:80 by container name", sub2="advanced routes send API, OAuth2, signal, gRPC on", logo="netbird", node="blue")

# --- row 2: the backends, grouped by destination zone, with the policy that admits NPM -----------
d.group("p40", "Personal-A backends", badge="VLAN 40 · zone Internal", family="Internal", cols=2, notes=[
    (None, "Allow NPM to media-01 web UIs · 5055, 7878, 8080, 8096, 8989, 9696"),
    (None, "Allow NPM to docker-main web UIs · 2283, 3000, 3001, 3002, 3003, 3004, 6060 · and CLI Proxy API · 8317"),
    (None, "Allow NPM to docker-blue Executor · 4788 · MeshCentral · 443 · Allow NPM to ansible-01 Semaphore · 3000")])
d.card("p40", "media", "media-01 · 192.168.40.42", badge="6 names", span=2, sub1="jellyfin 8096, seerr 5055, sonarr 8989, radarr 7878,", sub2="prowlarr 9696, qbittorrent 8080", logo="jellyfin", icons=["seerr", "sonarr", "radarr", "prowlarr", "qbittorrent"], node="red")
d.card("p40", "dmain", "docker-main · 192.168.40.35", badge="8 names", span=2, sub1="immich 2283, forgejo 3000, dashboard 3001, openwebui 3002,", sub2="dockhand 3003, appportal 3004, booklore 6060, aiproxy 8317", logo="docker", icons=["immich", "forgejo", "open-webui", "dockhand", "booklore"], node="grey")
d.card("p40", "dblue", "docker-blue · 192.168.40.39", badge="2", sub1="mcp 4788 (Executor)", sub2="mesh 443 (MeshCentral, HTTPS backend)", logo="docker", icons=["meshcentral"], node="blue")
d.card("p40", "ans", "ansible-01 · 192.168.40.36", badge="1", sub1="semaphore 3000", sub2="Semaphore advertises the HTTPS name", logo="ansible", icons=["semaphore"], node="blue")
d.group("p72", "Observability backends", badge="VLANs 72 and 73", family="Observability", cols=1, notes=[
    (None, "Allow NPM to monitor-01 web UIs · 3000, 8090, 9090"),
    (None, "Allow NPM to security-01 Wazuh · 443"),
    (None, "Allow NPM to splunk-siem web UI · 8000")])
d.card("p72", "mon", "monitor-01 · 192.168.73.2", badge="3", sub1="grafana 3000, prometheus 9090, peanut 8090", sub2="Grafana's root URL is the HTTPS name", logo="grafana", icons=["prometheus", "peanut"], node="blue")
d.card("p72", "sec", "security-01 · 192.168.72.2", badge="1", sub1="wazuh 443 · HTTPS backend", sub2="the Wazuh dashboard's own listener", logo="wazuh", node="grey")
d.card("p72", "spl", "splunk-siem · 192.168.72.3", badge="1", sub1="splunk 8000 · HTTPS backend", sub2="HEC, 1514 and 9997 stay direct", logo="splunk", node="grey")
d.group("p80", "Other destinations", family="Servers", cols=1, notes=[
    (None, "Allow NPM to alpha-prod-01 TS3 Manager · 9000")])
d.card("p80", "alpha", "alpha-prod-01 · 192.168.80.118", badge="1", sub1="ts3-manager 9000 · SERVERS-A, VLAN 80", sub2="voice, ServerQuery and Playit stay outside NPM", logo="teamspeak", node="purple")
d.card("p80", "self", "docker-network itself", badge="1", sub1="netbird: netbird-dashboard:80 on proxy", sub2="container name, no firewall hop", logo="netbird", node="blue")
d.card("p80", "inbound", "Admitted in to NPM on 443", sub1="HQ-WS001 192.168.65.20 from AlphaSec-Identity", sub2="Hawser agents on alpha-prod-01 and security-01", logo="unifi", icons=["windows-11", "dockhand"])

d.row("lan", "unifi", "certpath")
d.row("host")
d.row("p40", "p72", "p80")

# in
d.edge("client", "npm", "HTTPS 443 · the name's certificate is always certificate 1", color="blue", label_seg=1, label_x="mid:npm:-40")
# the certificate
d.edge("cf", "cert1", "TXT challenge through the Cloudflare API", color="grey", t_off=-30, y="gap:0:-12", label_seg=1)
d.edge("le", "cert1", "issues and renews npm-1", color="grey", t_off=30, y="gap:0:+12", label_seg=1)
# out
d.edge("npm", "p40", "HTTP to the listed ports", color="blue", s_off=-40, t_off=-200, y="gap:1:-14", label_seg=1, label_x="mid:p40:-200")
d.edge("npm", "p72", "HTTP; HTTPS to wazuh and splunk", color="blue", s_off=0, y="gap:1:+4", label_seg=1)
d.edge("npm", "p80", "HTTP 9000; netbird by container name", color="blue", s_off=40, y="gap:1:+22", label_seg=1, label_x="mid:p80:-140")

d.legend_family("External", "clients, or outside the lab"); d.legend_family("Internal", "UniFi, and the Internal zone"); d.legend_family("Access", "AlphaSec-Access")
d.legend_family("Observability", "AlphaSec-Observability"); d.legend_family("Servers", "AlphaSec-Servers")
d.legend_edge("HTTPS in, HTTP or HTTPS out", "solid", "blue"); d.legend_edge("certificate issuance", "solid", "grey")
for n in ("grey", "purple", "blue", "red"): d.legend_badge(f"runs on {n}-server", n)
d.footnote("Read on 2026-09-24: 33 proxy_host rows, 24 live and 9 soft-deleted; 24 generated files under /data/nginx/proxy_host; 24 UniFi records, one per live host. Every live host uses certificate 1 with Force SSL and HTTP/2; NPM's Public access-list label means no list is assigned, not public exposure.")
d.footnote("Proxy host 12, dashboard, forwards to 192.168.40.35:3001 where nothing has listened since the Homelab Dashboard container stopped on 2026-09-22; the host and its record remain. immich carries a 50,000 MiB body limit; aiproxy, mcp, mesh and dockhand run with buffering off and 3,600 s timeouts.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
