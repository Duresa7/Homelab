# Homarr

**Created:** 2026-09-27  
**Last updated:** 2026-09-28

I run Homarr 1.77.2 at [dashboard.alphasecunited.com](https://dashboard.alphasecunited.com) on `docker-main`. It replaces the [retired Homelab Dashboard](../../Archive/Platforms/Homelab%20Dashboard/README.md) at the same internal HTTPS name. I completed onboarding with the standard application account and verified a fresh login through HTTPS after restarting the container.

| Item | Value |
|---|---|
| Host | CT 110 `docker-main`, `grey-server`, `192.168.40.35`, VLAN 40 |
| Image | `ghcr.io/homarr-labs/homarr:v1.77.2` |
| Container | `homarr`, restart policy `unless-stopped` |
| Compose project | `/opt/docker/homarr/docker-compose.yml` |
| Persistent data | `/opt/docker/homarr/appdata` mounted at `/appdata`; embedded SQLite and Redis |
| Encryption key | `/opt/docker/homarr/.env`, mode `0600`; generated once and retained across restarts |
| Backend | `http://192.168.40.35:7575` |
| NPM | Proxy host 34, HTTP upstream `192.168.40.35:7575`, certificate 1, Force SSL, HTTP/2 and WebSockets enabled |
| DNS | UniFi local A record to `192.168.85.2`, TTL 300; public lookup returns NXDOMAIN |
| Firewall | TCP 7575 added to `Allow NPM to docker-main web UIs`; other selectors and ports preserved |
| Login | Standard application username and password; anonymous browser access reaches the login page |
| Initial settings | Analytics disabled; crawler indexing and following disabled |
| Integrations | Sonarr, Radarr, Prowlarr, qBittorrent, Seerr, Jellyfin, Proxmox, PeaNUT, Gluetun. Docker socket is not mounted |
| Logs | Docker `json-file`, 10 MiB per file, three files |

I use one private [Dashboard](https://dashboard.alphasecunited.com/boards/dashboard) as my desktop and mobile home. It contains all nine integrations, 32 website shortcuts with status checks and nine data widgets on one page. The separate Media and Infrastructure boards and the starter board were removed after consolidation.

Of the 32 retained shortcuts, 27 returned HTTP 200 in the earlier status check. Windows Admin Center and the Purple, Blue, Red and Green Proxmox interfaces timed out from Homarr; their checks remain enabled. Status is HTTP reachability from Homarr, not a successful authenticated session.

## Records and configuration

- [Shortcut and WUD removal](Documentation/Change%20Records/Shortcut%20and%20WUD%20Removal%20-%202026-09-27.md)

- [Website shortcuts and status checks](Documentation/Change%20Records/Website%20Shortcuts%20-%202026-09-27.md)
- [App shortcut configuration](Configuration/App-Shortcuts.json)
- [Single dashboard consolidation](Documentation/Change%20Records/Single%20Dashboard%20-%202026-09-27.md)

- [Media and infrastructure integrations](Documentation/Change%20Records/Media%20and%20Infrastructure%20Integrations%20-%202026-09-27.md)

- [Deployment and verification](Documentation/Change%20Records/Deployment%20-%202026-09-27.md)
- [Compose reference](Configuration/docker-compose.yml)
- [Environment template](Configuration/.env.example)
- [Placement assessment](../../Infrastructure/Compute/Galaxy/Documentation/Homarr%20Placement%20Research%20-%202026-09-27.md)

I manage the deployment from `/opt/docker/homarr` with Docker Compose. I validate with `docker compose config --quiet`, inspect state with `docker compose ps`, and test `/api/health/ready` through HTTPS. The image has no Docker health check; HTTP readiness and authenticated requests are the verification paths. For upgrades I review the official release notes, change the pinned image tag, pull it and run `docker compose up -d`, then repeat the HTTPS and login checks. The `.env` key and `appdata` directory must stay together; replacing the encryption key breaks access to encrypted integration secrets.

On 2026-09-28 I renamed the BookLore shortcut to BookOrbit and switched its icon to the application favicon. The destination remains `https://booklore.alphasecunited.com`, and the Homarr status check returned HTTP 200. [Migration](../BookOrbit/Documentation/Change%20Records/Migration%20from%20BookLore%20-%202026-09-28.md).
