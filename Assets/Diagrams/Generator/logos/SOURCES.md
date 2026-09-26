# Logo sources

**Created:** 2026-09-24  
**Last updated:** 2026-09-25

Every file here is a square-viewBox SVG produced by `build_logos.py` from `_raw/` (dashboard-icons downloads, one PNG each for the four PNG-only names) and `_si/` (simple-icons paths filled with the brand hex). The diagram library embeds each file once as a base64 data URI inside a `<symbol>` and places it with `<use>`, so a rendered diagram carries no external reference.

Preference order was dashboard-icons full-colour SVG, then simple-icons, then Brandfetch, then a neutral glyph. Brandfetch was queried for the three PNG-only products and returned nothing usable, so those stay as downscaled PNGs wrapped in SVG.

| File | Source | Source name | Licence or usage note | Placed |
|---|---|---|---|---|
| `action1.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `action1` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. a wide wordmark (viewBox 300 x 53); readable only at 28 px or more, so it is mentioned in card text rather than drawn as a mini icon. | no |
| `amd.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `amd` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `ansible.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `ansible` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `apc.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `apc` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. used for UPS-02; the model is not drawn because it is not in the brief. | yes |
| `apple.svg` | simple-icons 16.32.0 (node_modules under .scratch/reorg/logo-tools) | `apple` | CC0-1.0 for the icon set; the mark itself stays the owner's trademark. simple-icons `siApple` filled with 000000; stands for the Mac identity on ssh-key-lifecycle. dashboard-icons has no Apple mark. | yes |
| `booklore.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `booklore` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `caddy.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `caddy` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `cadvisor.svg` | dashboard-icons PNG, wrapped | `cadvisor` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. PNG-only in dashboard-icons (200 x 257); downscaled to 56 x 72 and wrapped in a square SVG. | yes |
| `cloudflare.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `cloudflare` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `cloudflare-zero-trust.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `cloudflare-zero-trust` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | no |
| `cloudflared.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `cloudflared` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `coolify.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `coolify` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `debian.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `debian-linux` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. dashboard-icons `debian-linux` (the `debian` name is a 404). | yes |
| `discord.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `discord` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `docker.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `docker` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `dockhand.svg` | dashboard-icons PNG, wrapped | `dockhand` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. PNG-only in dashboard-icons; Brandfetch's search for `dockhand` matched an unrelated company. Downscaled to 72 px and wrapped in an SVG. | yes |
| `entra-id.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `entra-id` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `flaresolverr.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `flaresolverr` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes, since 2026-09-25 on media-stack |
| `forgejo.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `forgejo` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `github.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `github` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | no |
| `gluetun.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `gluetun` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `grafana.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `grafana` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `immich.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `immich` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `intel.svg` | simple-icons 16.32.0 (node_modules under .scratch/reorg/logo-tools) | `intel` | CC0-1.0 for the icon set; the mark itself stays the owner's trademark. simple-icons `siIntel` filled with the brand hex 0071C5; dashboard-icons has no Intel mark. | yes |
| `jellyfin.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `jellyfin` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `kali-linux.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `kali-linux` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `letsencrypt.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `lets-encrypt` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. the wildcard certificate on nginx-proxy-manager; added 2026-09-25. | yes |
| `linux.svg` | simple-icons 16.32.0 (node_modules under .scratch/reorg/logo-tools) | `linux` | CC0-1.0 for the icon set; the mark itself stays the owner's trademark. simple-icons `siLinux` filled with FCC624; not currently placed on any diagram. | no |
| `meshcentral.svg` | dashboard-icons PNG, wrapped | `meshcentral` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. PNG-only in dashboard-icons (base: png); Brandfetch returned no assets for meshcentral.com. The 303 px PNG was downscaled to 72 px with PIL and wrapped in an SVG. | yes |
| `microsoft-intune.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `microsoft-intune` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `netbird.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `netbird` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `nginx-proxy-manager.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `nginx-proxy-manager` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `node-exporter.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `prometheus-node-exporter` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. dashboard-icons `prometheus-node-exporter`. | yes |
| `nut.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `network-ups-tools` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. dashboard-icons `network-ups-tools`; not legible at 16 px, so it is not placed on a card. | no |
| `nvidia.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `nvidia` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `ollama.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `ollama` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `open-webui.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `open-webui` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `peanut.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `peanut` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `playit.svg` | dashboard-icons PNG, wrapped | `playit-gg` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. dashboard-icons `playit-gg`, PNG-only; Brandfetch returned no assets for playit.gg. Downscaled to 72 px and wrapped in an SVG. | yes |
| `podman.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `podman` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. SC4S runs in Podman on splunk-siem; drawn as a mini icon on the SC4S card; added 2026-09-25 for splunk. | yes |
| `postgresql.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `postgresql` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. Immich's database container and its dump on immich-migration; added 2026-09-25. | yes |
| `prometheus.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `prometheus` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `proton-vpn.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `proton-vpn` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `prowlarr.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `prowlarr` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes, since 2026-09-25 on media-stack |
| `proxmox.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `proxmox` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `qbittorrent.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `qbittorrent` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes, since 2026-09-25 on media-stack |
| `radarr.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `radarr` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `redis.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `redis` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. Immich's cache container on immich-migration; added 2026-09-25. | yes |
| `rocky-linux.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `rocky-linux` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `rustdesk.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `rustdesk` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `seerr.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `seerr` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `semaphore.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `semaphore` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `sonarr.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `sonarr` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `splunk.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `splunk` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `teamspeak.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `teamspeak` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `toshiba.svg` | simple-icons 16.32.0 (node_modules under .scratch/reorg/logo-tools) | `toshiba` | CC0-1.0 for the icon set; the mark itself stays the owner's trademark. simple-icons `siToshiba` filled with the brand hex FF0000; dashboard-icons' `toshiba` is an 800 x 122 wordmark that is a 4 px strip at card size. The destination drive on immich-migration; added 2026-09-25. | yes |
| `traefik.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `traefik` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `ubiquiti.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `ubiquiti` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | no |
| `ubuntu.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `ubuntu-linux` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. dashboard-icons `ubuntu-linux` (the `ubuntu` name is a 404). | yes |
| `unifi.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `unifi` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. the UniFi `U` mark; used for the gateway, switches and access point. | yes |
| `ups.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `ups` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `verizon.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `verizon` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. the ISP behind WAN 1's ONT, as named in the brief. | yes |
| `virustotal.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `virustotal` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. the VirusTotal lookup Wazuh runs on file-integrity events; added 2026-09-25 for wazuh. | yes |
| `wazuh.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `wazuh` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `western-digital.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `western-digital` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. the retired source drive on immich-migration; added 2026-09-25. | yes |
| `windows-11.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `windows-11` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes |
| `windows-server.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `microsoft-windows` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. dashboard-icons has no Windows Server mark; this is `microsoft-windows`, the four-pane Windows logo, used for the three Windows Server 2025 guests. | yes |
| `wireguard.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `wireguard` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only | yes, since 2026-09-25 on netbird |
| `wud.svg` | dashboard-icons (homarr-labs) via cdn.jsdelivr.net | `whats-up-docker` | MIT for the repository; each mark stays the trademark of its owner and is used for identification only. What's Up Docker, the `wud` scrape job on the six Compose hosts; added 2026-09-25 for prometheus. | yes |

## Drawn without a logo

The library draws a neutral glyph (rounded square with short text) where no obtainable mark exists or where a mark would assert something the brief does not state:

- `WAN 2`: the brief names no provider for the second uplink.
- `Jedi PC`: the brief gives its address and role but not its operating system.
- VLAN chips (`0` to `85`) on network-zones: VLAN IDs, not products.
- Text-only products with no logo in either source: Moonbase and the Moonfin clients (drawn with the Jellyfin mark), Corosync, Executor, SSH Manager MCP, Docker MCP Gateway (the Docker whale stands for the Docker hosts), TS3 Manager, SC4S, Hawser Edge, App Portal, Homelab Dashboard, the internal docs site, CLI Proxy API, Windows Admin Center, Active Directory (identity is shown with the Entra ID mark on HQ-MGT01 and the flow label).

## Rebuild

```
python3 logos/build_logos.py
```

`_raw/` and `_si/` are the inputs and stay in place so the set can be regenerated. Adding a product means adding one row to `LOGOS` in `build_logos.py` and dropping the source file into `_raw/` or `_si/`.
