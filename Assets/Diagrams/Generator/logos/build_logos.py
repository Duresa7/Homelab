#!/usr/bin/env python3
"""Normalise raw logo files into square-viewBox SVGs under logos/.

Sources: logos/_raw/<name>.svg (dashboard-icons), logos/_si/<name>.svg
(simple-icons with brand hex fill), logos/_raw/<name>.png (dashboard-icons
PNG-only entries, wrapped in an SVG). Output is logos/<key>.svg with a square
viewBox and the artwork centred. Run: python3 logos/build_logos.py
"""
import base64, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW, SI = os.path.join(HERE, "_raw"), os.path.join(HERE, "_si")

# key -> (source kind, source file stem)
LOGOS = {
    "proxmox": ("di", "proxmox"), "unifi": ("di", "unifi"), "ubiquiti": ("di", "ubiquiti"),
    "cloudflare": ("di", "cloudflare"), "cloudflare-zero-trust": ("di", "cloudflare-zero-trust"),
    "cloudflared": ("di", "cloudflared"), "proton-vpn": ("di", "proton-vpn"), "verizon": ("di", "verizon"),
    "splunk": ("di", "splunk"), "wazuh": ("di", "wazuh"), "prometheus": ("di", "prometheus"),
    "grafana": ("di", "grafana"), "docker": ("di", "docker"), "nginx-proxy-manager": ("di", "nginx-proxy-manager"),
    "netbird": ("di", "netbird"), "caddy": ("di", "caddy"), "traefik": ("di", "traefik"),
    "coolify": ("di", "coolify"), "teamspeak": ("di", "teamspeak"), "jellyfin": ("di", "jellyfin"),
    "immich": ("di", "immich"), "ansible": ("di", "ansible"), "semaphore": ("di", "semaphore"),
    "rocky-linux": ("di", "rocky-linux"), "kali-linux": ("di", "kali-linux"),
    "ubuntu": ("di", "ubuntu-linux"), "debian": ("di", "debian-linux"),
    "forgejo": ("di", "forgejo"), "ollama": ("di", "ollama"), "open-webui": ("di", "open-webui"),
    "rustdesk": ("di", "rustdesk"), "discord": ("di", "discord"), "qbittorrent": ("di", "qbittorrent"),
    "sonarr": ("di", "sonarr"), "radarr": ("di", "radarr"), "prowlarr": ("di", "prowlarr"),
    "flaresolverr": ("di", "flaresolverr"), "gluetun": ("di", "gluetun"), "seerr": ("di", "seerr"),
    "booklore": ("di", "booklore"), "windows-11": ("di", "windows-11"), "windows-server": ("di", "microsoft-windows"),
    "microsoft-intune": ("di", "microsoft-intune"), "entra-id": ("di", "entra-id"), "action1": ("di", "action1"),
    "peanut": ("di", "peanut"), "nut": ("di", "network-ups-tools"), "apc": ("di", "apc"), "ups": ("di", "ups"),
    "wireguard": ("di", "wireguard"), "nvidia": ("di", "nvidia"), "amd": ("di", "amd"),
    "node-exporter": ("di", "prometheus-node-exporter"), "github": ("di", "github"),
    "wud": ("di", "whats-up-docker"), "virustotal": ("di", "virustotal"),
    "intel": ("si", "intel"), "linux": ("si", "linux"), "apple": ("si", "apple"),
    "letsencrypt": ("di", "lets-encrypt"), "postgresql": ("di", "postgresql"), "redis": ("di", "redis"),
    "western-digital": ("di", "western-digital"), "podman": ("di", "podman"), "toshiba": ("si", "toshiba"),
    "meshcentral": ("png", "meshcentral"), "dockhand": ("png", "dockhand"),
    "playit": ("png", "playit-gg"), "cadvisor": ("png", "cadvisor"),
}

def num(s):
    m = re.match(r"\s*([0-9.]+)", s or ""); return float(m.group(1)) if m else None

def wrap_svg(text):
    m = re.search(r"<svg\b([^>]*)>", text, re.S)
    if not m: raise ValueError("no <svg> root")
    attrs = m.group(1); inner = text[m.end():text.rfind("</svg>")]
    vb = re.search(r'viewBox="([^"]+)"', attrs)
    if vb:
        x, y, w, h = [float(v) for v in vb.group(1).replace(",", " ").split()]
    else:
        w = num(re.search(r'\swidth="([^"]+)"', attrs).group(1)); h = num(re.search(r'\sheight="([^"]+)"', attrs).group(1)); x = y = 0.0
    s = max(w, h)
    keep = re.sub(r'\s(width|height|x|y|viewBox)="[^"]*"', "", attrs)
    if "xmlns=" not in keep: keep += ' xmlns="http://www.w3.org/2000/svg"'
    inner_svg = f'<svg{keep} x="{(s-w)/2:g}" y="{(s-h)/2:g}" width="{w:g}" height="{h:g}" viewBox="{x:g} {y:g} {w:g} {h:g}">{inner}</svg>'
    ns = ' xmlns:xlink="http://www.w3.org/1999/xlink"' if "xlink:" in text else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg"{ns} viewBox="0 0 {s:g} {s:g}">{inner_svg}</svg>'

def wrap_png(data):
    w, h = struct.unpack(">II", data[16:24]); s = max(w, h)
    b64 = base64.b64encode(data).decode()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}">'
            f'<image x="{(s-w)/2:g}" y="{(s-h)/2:g}" width="{w}" height="{h}" href="data:image/png;base64,{b64}"/></svg>')

def main():
    import xml.etree.ElementTree as ET
    for key, (kind, stem) in sorted(LOGOS.items()):
        if kind == "png":
            out = wrap_png(open(os.path.join(RAW, stem + ".png"), "rb").read())
        else:
            src = os.path.join(RAW if kind == "di" else SI, stem + ".svg")
            out = wrap_svg(open(src, encoding="utf-8").read())
        ET.fromstring(out)
        with open(os.path.join(HERE, key + ".svg"), "w", encoding="utf-8") as f: f.write(out)
        print(f"{key:24} {kind:4} {len(out):7d} B")

if __name__ == "__main__": main()
