# Homarr

**Created:** 2026-09-27  
**Last updated:** 2026-11-01

I retired Homarr from `docker-main` on 2026-11-01. It ran Homarr 1.77.2 from `ghcr.io/homarr-labs/homarr:v1.77.2` as `homarr`, published on `192.168.40.35:7575` and reached at `dashboard.alphasecunited.com` through NPM proxy host 34. Its data and encryption key lived under `/opt/docker/homarr`. I deployed it on 2026-09-27 to replace the [retired Homelab Dashboard](../Homelab%20Dashboard/README.md) at the same name.

I removed the deployment, its data and encryption key, the image, the proxy host, the DNS record, the Homarr-to-Grey firewall policy and TCP 7575 on the NPM-to-docker-main policy, the `homarr@pve` Proxmox account and token, the Gluetun control API I had opened on `media-01` for its VPN widget, the fleet-update entry, and the stored integration credentials. I kept no backup of the application or its data. Nothing replaces it at `dashboard.alphasecunited.com`.

- [Retirement and verification](Documentation/Change%20Records/Retirement%20-%202026-11-01.md)
- [Final HTTPS, proxy and DNS checks](Evidence/Retirement%20-%202026-11-01/Exports/Final-Verification.json)

## What it was

| Item | Value while running |
|---|---|
| Host | CT 110 `docker-main`, `grey-server`, `192.168.40.35`, VLAN 40 |
| Compose project | `/opt/docker/homarr/docker-compose.yml`, persistent `/appdata`, encryption key in a mode-0600 `.env` |
| NPM | Proxy host 34, HTTP upstream `192.168.40.35:7575`, certificate 1, Force SSL, HTTP/2 and WebSockets |
| DNS | UniFi local A record `6ab90b1425574794b9328224` to `192.168.85.2`, TTL 300 |
| Firewall | TCP 7575 on `Allow NPM to docker-main web UIs`; `Allow Homarr to Grey Proxmox API` for TCP 8006 |
| Login | Standard application account |
| Integrations | Sonarr, Radarr, Prowlarr, qBittorrent, Seerr, Jellyfin, Proxmox through `homarr@pve!dashboard`, PeaNUT, and Gluetun through a GET-only control API key |
| Board | One private dashboard with nine integrations, 32 website shortcuts and nine data widgets |

## Retained records and configuration

- [Deployment and verification](Documentation/Change%20Records/Deployment%20-%202026-09-27.md)
- [Media and infrastructure integrations](Documentation/Change%20Records/Media%20and%20Infrastructure%20Integrations%20-%202026-09-27.md)
- [Single dashboard consolidation](Documentation/Change%20Records/Single%20Dashboard%20-%202026-09-27.md)
- [Website shortcuts and status checks](Documentation/Change%20Records/Website%20Shortcuts%20-%202026-09-27.md)
- [Shortcut and WUD removal](Documentation/Change%20Records/Shortcut%20and%20WUD%20Removal%20-%202026-09-27.md)
- [Compose reference](Configuration/docker-compose.yml) and [environment template](Configuration/.env.example)
- [App shortcut configuration](Configuration/App-Shortcuts.json)
- [Gluetun control API role template](Configuration/gluetun-homarr-auth.toml.example), moved here from the Media Stack configuration when I removed the API
- [Placement assessment](../../Infrastructure/Compute/Galaxy/Documentation/Homarr%20Placement%20Research%20-%202026-09-27.md)

On 2026-09-28 I renamed the BookLore shortcut to BookOrbit ([migration](../../../Platforms/BookOrbit/Documentation/Change%20Records/Migration%20from%20BookLore%20-%202026-09-28.md)), and on 2026-10-31 I pointed the Executor shortcut at `https://executor.alphasecunited.com` ([Executor 2 Migration](../../../Platforms/Executor/Documentation/Change%20Records/Executor%202%20Migration%20-%202026-10-31.md)). Both shortcuts went away with the application.
