#!/usr/bin/env python3
"""media-stack: the request, acquisition, VPN-isolated download, storage and
playback paths on media-01 (remake of the 2026-07-20 media-stack and pipeline
diagrams, merged). Facts: Platforms/Media Stack/README.md (services, ports,
storage paths), Documentation/Architecture.md (traffic split, bind mount),
Documentation/Runbook.md (health baseline, kill switch, port sync, jellyseerr
name), Guides/Media-Stack.md (versions and guest size verified 2026-09-24),
Change Records/Anime Library Routing and Moonbase Plugin Installation, and the
NPM proxy-host inventory and UniFi firewall record for the published names."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
from diagram import Diagram

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "media-stack.svg")
d = Diagram("media-stack", "Media stack on media-01",
            "LXC 842 on red-server, 192.168.40.42 on VLAN 40, 2 vCPU and 4 GiB. Seerr takes the request, Sonarr and Radarr grab it, qBittorrent downloads only through Gluetun and Proton VPN, Jellyfin plays the hard-linked file",
            source="Platforms/Media Stack/README.md, Platforms/Media Stack/Documentation/Architecture.md, Platforms/Media Stack/Documentation/Runbook.md, Guides/Media-Stack.md",
            width=1640, card_w=200, row_gap=64)

# --- row 0: who uses it, and the proxy that publishes it -------------------------
d.group("viewers", "Viewers", badge="LAN", family="External")
d.card("viewers", "moonfin", "Moonfin clients", sub1="Jellyfin clients, Moonbase 2.1.0 plugin", sub2="settings sync, Seerr single sign-on", logo="jellyfin")
d.card("viewers", "browser", "Browser", sub1="requests in Seerr, the *arr web UIs", sub2="through the internal HTTPS names", logo="glyph:WEB")
d.group("npm", "Access-A", badge="VLAN 85", family="Access")
d.card("npm", "npmc", "Nginx Proxy Manager 2.15.1", sub1="docker-network 192.168.85.2", sub2="six names under alphasecunited.com", logo="nginx-proxy-manager", node="blue")
d.group("unifi", "UniFi", badge="Ahsoka Gateway", family="Internal")
d.card("unifi", "gw", "Local DNS and zone firewall", sub1="six A records answer 192.168.85.2", sub2="Allow NPM to media-01 web UIs: six ports", logo="unifi")

# --- row 1: request and playback, plus the fleet services on the same guest ---------
d.group("req", "Request and playback", badge="media-01 · Compose project media-stack", family="Internal")
d.card("req", "jellyfin", "Jellyfin 12.1.0", sub1=":8096 · Movies, TV Shows, Anime", sub2="Quick Sync via /dev/dri/renderD128", logo="jellyfin", node="red")
d.card("req", "seerr", "Seerr 3.4.1", sub1=":5055 · container still named jellyseerr", sub2="libraries synced, SSO via Moonbase", logo="seerr", node="red")
d.group("side", "Beside the stack", badge="media-01 · own Compose projects", family="Internal")
d.card("side", "wazuh", "Wazuh agent 4.14.6-1", sub1="ID 008 · group default", sub2="TCP 1514 to security-01", logo="wazuh", node="red")
d.card("side", "cadv", "cAdvisor 0.60.6", sub1=":9101 · job cadvisor", sub2="scraped by monitor-01", logo="cadvisor", node="red")
d.card("side", "wud", "What's Up Docker 9.1.0", sub1=":9102 · job wud", sub2="flags image updates", logo="wud", node="red")
d.card("side", "hawser", "Hawser 0.2.48", sub1="Dockhand edge agent", sub2="managed from docker-main", logo="dockhand", node="red")

# --- row 2: acquisition, and the namespace that is the only way out ------------------
d.group("acq", "Acquisition", badge="media-01 · Compose project media-stack", family="Internal")
d.card("acq", "prowlarr", "Prowlarr 2.6.5", sub1=":9696 · 1337x, EZTV, Nyaa.si", sub2="indexers to Sonarr and Radarr", logo="prowlarr", node="red")
d.card("acq", "flare", "FlareSolverr 3.5.2", sub1="no published port", sub2="solves Cloudflare challenges", logo="flaresolverr", node="red")
d.card("acq", "sonarr", "Sonarr 4.0.20", sub1=":8989 · tv and anime roots", sub2="HD-1080p, anime Remux-1080p", logo="sonarr", node="red")
d.card("acq", "radarr", "Radarr 6.4.4", sub1=":7878 · root /data/media/movies", sub2="imports as hard links, not copies", logo="radarr", node="red")
d.group("vpn", "Gluetun network namespace", badge="network_mode: service:gluetun", family="Dmz", notes=[
    (None, "qBittorrent has no network of its own; the tunnel's"),
    (None, "firewall is its kill switch, and Gluetun must be"),
    (None, "healthy before qBittorrent is allowed to start")])
d.card("vpn", "qbit", "qBittorrent 5.2.3", sub1=":8080, published by Gluetun", sub2="100-pattern payload filter, no UPnP", logo="qbittorrent", node="red")
d.card("vpn", "gluetun", "Gluetun", sub1="WireGuard to Proton, kill switch", sub2="forwarded port written into qBittorrent", logo="gluetun", node="red")

# --- row 3: the HDD on the node, and the outside world the tunnel reaches --------------
d.group("hdd", "red-server · HDD", badge="ext4 · backup=0", family="Mgmt", accent="red")
d.card("hdd", "tv", "/data/media/tv", sub1="Sonarr root, HD-1080p", sub2="Jellyfin TV Shows library", logo="glyph:TV")
d.card("hdd", "anime", "/data/media/anime", sub1="Sonarr root, anime Remux-1080p", sub2="Jellyfin Anime library, AniList first", logo="glyph:ANI")
d.card("hdd", "movies", "/data/media/movies", sub1="Radarr root", sub2="Jellyfin Movies library", logo="glyph:MOV")
d.card("hdd", "downloads", "/data/downloads", sub1="qBittorrent categories", sub2="completed torrents land here", logo="glyph:DL")
d.group("outside", "Outside the lab", family="External")
d.card("outside", "peers", "Torrent peers", sub1="reached only through the tunnel", sub2="inbound on Proton's forwarded port", logo="glyph:P2P")
d.card("outside", "proton", "Proton VPN", sub1="WireGuard P2P endpoint", sub2="egress check returns Proton", logo="proton-vpn")

d.row("viewers", "npm", "unifi")
d.row("req", "side")
d.row("acq", "vpn")
d.row("hdd", "outside")

def align(src, dst):
    """s_off that makes a vertical edge from src to dst a single straight line."""
    d._layout(); s, t = d.items[src], d.items[dst]
    return (t.x + t.w / 2) - (s.x + s.w / 2)

# viewers reach everything through NPM; NPM reaches the two front doors on the guest
d.edge("viewers", "npm", "", color="blue", arrows="both")
d.edge("npmc", "jellyfin", "jellyfin :8096 · stream, Moonfin web app", color="blue", s_off=-30, y="gap:0:-12", label_seg=1, label_x="mid:seerr:+60")
d.edge("npmc", "seerr", "seerr :5055", color="blue", s_off=30, y="gap:0:+12", label_seg=1, label_x="mid:npmc:-140")
# the request path
d.edge("seerr", "sonarr", "TV and anime requests", color="grey", s_off=-20, t_off=-20, y="gap:1:-8", label_seg=1, label_x="between:seerr,sonarr")
d.edge("seerr", "radarr", "movie requests", color="grey", s_off=20, t_off=-20, y="gap:1:+8", label_seg=1, label_x="mid:radarr:-80")
d.edge("radarr", "qbit", "grab · completed downloads import as hard links", color="grey", arrows="both",
       from_side="top", to_side="top", s_off=40, t_off=-30, y="gap:1:-24", label_seg=1, label_x="mid:qbit:-70", label_anchor="middle")
# what lands on the HDD, and what Jellyfin reads from it
d.edge("sonarr", "tv", "TV root", color="grey", s_off=-16, t_off=40, y="gap:2:-18", label_x="mid:tv:+40", label_y="gap:2:+6")
d.edge("sonarr", "anime", "anime root", color="grey", s_off=16, y="gap:2:-6", label_x="mid:anime", label_y="gap:2:+8")
d.edge("radarr", "movies", "movies root", color="grey", y="gap:2:+6", label_x="mid:movies", label_y="gap:2:+18")
d.edge("qbit", "downloads", "writes completed torrents", color="grey", t_off=-60, y="gap:2:+18", label_x="mid:qbit:-80", label_y="gap:2:+2")
d.edge("hdd", "jellyfin", "Jellyfin reads the three libraries at /media", color="grey", from_side="left", to_side="bottom", x="left", y="gap:1:+22",
       label_x="left:+8", label_anchor="start", label_y="gap:1:+22")
# the only egress from the namespace
d.edge("gluetun", "proton", "WireGuard tunnel, kill switch on", style="dashed", color="teal", s_off=align("gluetun", "proton"))
d.edge("proton", "peers", "", style="dashed", color="teal", arrows="both")

d.legend_family("External", "viewers, or outside the lab"); d.legend_family("Access", "AlphaSec-Access"); d.legend_family("Internal", "media-01 on Personal-A, VLAN 40")
d.legend_family("Dmz", "VPN-isolated network namespace"); d.legend_family("Mgmt", "the node's HDD")
d.legend_edge("HTTPS through the internal names", "solid", "blue"); d.legend_edge("requests, grabs, imports and reads", "solid", "grey"); d.legend_edge("WireGuard tunnel", "dashed", "teal")
d.legend_badge("runs on red-server", "red"); d.legend_badge("runs on blue-server", "blue")
d.footnote("Every image tracks latest; an update is a bounded change verified through the runbook. NPM publishes jellyfin, seerr, sonarr, radarr, prowlarr and qbittorrent, and the UniFi policy Allow NPM to media-01 web UIs admits 192.168.85.2 to exactly those six ports.")
d.footnote("Prowlarr and the media services keep ordinary VLAN 40 egress; only qBittorrent leaves through the tunnel. Downloads and libraries share one ext4 filesystem, so an import is a hard link; /data/transcodes is Jellyfin's scratch space.")
d.footnote("/data is the node's 1 TB HDD (916 GiB usable) bind-mounted into CT 842 as mp0; it is not in vzdump and the media is replaceable. The 100 GiB NVMe root keeps /opt/media-stack, the application configs and databases and the Jellyfin cache, which is what a rebuild needs.")
d.render(OUT, png=os.environ.get("PNG") == "1", readme_width=int(os.environ.get("README_W", "0")) or None)
