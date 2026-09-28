# Media and Infrastructure Integrations

**Created:** 2026-09-27  
**Last updated:** 2026-09-27

**Status:** Complete. Ten integrations and both private boards verified.

**Subsequent layout correction, 2026-09-27:** I consolidated both boards into one dashboard. The [single-dashboard record](Single%20Dashboard%20-%202026-09-27.md) supersedes the board layout described below; all ten integrations remain configured.

I connected Homarr 1.77.2 to the six media services, Galaxy, PeaNUT, Gluetun and What's Up Docker on `docker-main`. I created private [Media](https://dashboard.alphasecunited.com/boards/media) and [Infrastructure](https://dashboard.alphasecunited.com/boards/infrastructure) boards. Media is my desktop and mobile home board. The existing starter `dashboard` board remains available.

## Connections and boards

| Integration | Endpoint | Authentication and use |
|---|---|---|
| Sonarr | `https://sonarr.alphasecunited.com` | Existing API key; release calendar |
| Radarr | `https://radarr.alphasecunited.com` | Existing API key; release calendar |
| Prowlarr | `https://prowlarr.alphasecunited.com` | Existing API key; indexer status |
| qBittorrent | `https://qbittorrent.alphasecunited.com` | Standard application credentials; download status |
| Seerr | `https://seerr.alphasecunited.com` | Existing API key; request list. The container is still named `jellyseerr`, but the deployed application is Seerr |
| Jellyfin | `https://jellyfin.alphasecunited.com` | Standard application credentials; active streams and recently added media |
| Proxmox Galaxy | `https://grey.alphasecunited.com:8006` | Dedicated `homarr@pve!dashboard` API token; cluster health |
| PeaNUT | `https://peanut.alphasecunited.com` | Standard application credentials; UPS-02 battery, load and voltage |
| Gluetun | `http://192.168.40.42:8000` | Dedicated GET-only API key; VPN status |
| WUD docker-main | `https://wud.alphasecunited.com` | Existing host-specific service credentials; monitored containers and available updates |

The Media board has six service shortcuts and six data widgets. Infrastructure has three shortcuts and four widgets. Both boards have a 12-column base layout and require login. Jellyfin's location display is disabled. I made no media requests, download queue changes, container updates or guest power changes while validating these widgets. The separately approved Gluetun/qBittorrent recreation is recorded below. WUD here covers `docker-main`, not all six WUD instances.

## Proxmox access

I created a dedicated API user and privilege-separated token. Both have `PVEAuditor` at `/`, propagated to descendants. The new token is held in the approved credential vault and encrypted by Homarr; it cannot modify guests through the granted role.

The first connection timed out. UniFi's old dashboard allowance had been removed when the earlier application was retired. I added policy `6ab919b425574794b932ace9`, `Allow Homarr to Grey Proxmox API`: IPv4 TCP, source `192.168.40.35` in Internal, destination `192.168.70.10` in AlphaSec-Mgmt, destination port 8006, index 10005. Readback confirmed the exact selectors and enabled state. The Proxmox Datacenter firewall already includes `docker-main` in `pve_svc_clients` for TCP 8006; I left it unchanged.

After access was allowed, the IP-based URL failed hostname validation. Grey presents a public certificate for `grey.alphasecunited.com`; using that existing DNS name fixed the mismatch. I removed the unnecessary Galaxy CA I had briefly imported into Homarr. No TLS bypass or hostname exception remains.

The [Homarr Proxmox documentation](https://homarr.dev/docs/integrations/proxmox/) describes the auditor role and token fields. I verified the selected release's validation and router definitions before using its authenticated application API.

## WUD HTTPS

The initial WUD connection test passed because `/api/app` is accessible, but the widget failed against protected `/api/containers`. The standard application credentials returned 401; this WUD deployment uses the distinct service credential established during the [September 13 exporter migration](../../../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-13.md).

Homarr 1.77.2 sends WUD Basic authentication only to an HTTPS URL. I added NPM proxy host 35, `wud.alphasecunited.com`, forwarding HTTP to `192.168.40.35:9102`, using certificate 1 with Force SSL, HTTP/2 and WebSockets. Existing WUD authentication remains enabled. UniFi DNS record `6ab91af825574794b932b0d5` resolves this name to `192.168.85.2`, TTL 300. TCP 9102 joins the existing NPM-to-docker-main policy; its source, destination and other ports are preserved.

NPM readback reported the host online and 25 live hosts. `nginx -t` passed, HTTPS `/api/app` returned 200 with TLS verification result 0, and Homarr's authenticated WUD widget returned 12 monitored containers and three available updates. UniFi readback returned 31 static DNS records, including the new record. The public DNS check returned NXDOMAIN.

## Verification

I authenticated afresh and queried each widget through Homarr after saving its integration. The final [verification export](../../Evidence/Integrations%20-%202026-09-27/Exports/Verification.json) records the capture time and results.

| Check | Observed result |
|---|---|
| Calendar | Both Sonarr and Radarr returned data successfully |
| Downloads | qBittorrent returned jobs and status |
| Requests | Seerr returned 20 requests |
| Playback | Jellyfin returned one active session initially and zero in the final check; both requests succeeded |
| Recently added | Jellyfin returned ten entries |
| Indexers | Prowlarr returned three indexers |
| UPS | PeaNUT returned one monitored UPS |
| VPN | Gluetun VPN and DNS both running |
| Container updates | WUD returned statistics successfully |
| Cluster | Five nodes, six LXCs, 15 VM entries including templates, 13 storage entries |
| Browser | Fresh authenticated Chrome session loaded 12 Media items and seven Infrastructure items; no page errors or tested error indicators |

The request-list API initially rejected my verification call because I had omitted its required status and recent-day filters; I corrected the call and it passed. This was not a Seerr service failure.

The [board export](../../Evidence/Integrations%20-%202026-09-27/Exports/Boards.json) captures widget options, layout and integration references without credentials or user identity metadata. [NPM readback](../../Evidence/Integrations%20-%202026-09-27/Exports/NPM-WUD.json) contains only the new proxy's non-secret fields. These are filtered exports, not complete terminal transcripts. No raw transcript or screenshot is retained for credential handling, API mutations, firewall/DNS changes, browser verification or Gluetun proposal validation; the observed results are recorded here.

## Gluetun control API

Gluetun runs under Compose profile `vpn`; qBittorrent shares its network namespace. Initially, port 8000 was not published and control requests without authentication returned 401. I prepared a narrow Compose override and GET-only auth role, validated the override against the live project, and explained that recreating these two containers would briefly interrupt downloads. I proceeded after confirmation to continue.

I merged the validated change into `/opt/media-stack/compose.yml`: publish `192.168.40.42:8000:8000/tcp` and change `FIREWALL_INPUT_PORTS` from `8080` to `8080,8000`. I generated a dedicated API token, stored it in the approved credential vault, and installed `/opt/media-stack/config/gluetun/auth/config.toml` at mode 0600, inside a mode-0700 directory already covered by the existing `/gluetun` mount. The [authentication template](../../../Media%20Stack/Configuration/gluetun-homarr-auth.toml.example) and [Compose reference](../../../Media%20Stack/Configuration/compose.example.yml) capture the deployed shape without credentials.

The role permits only `GET /v1/vpn/status`, `GET /v1/dns/status`, `GET /v1/publicip/ip` and `GET /v1/vpn/settings`. It grants no VPN stop, start or settings-write route. [Gluetun's control-server documentation](https://raw.githubusercontent.com/qdm12/gluetun-wiki/main/setup/advanced/control-server.md) confirms that loading the auth file requires a restart.

After candidate validation returned exit 0, I recreated only `gluetun` and `qbittorrent` using Compose profile `vpn`, `--no-deps`, `--force-recreate` and `--pull never`. Compose reported Gluetun healthy before starting qBittorrent and exited 0. No image update was requested.

Post-change verification showed Gluetun healthy, qBittorrent running in the new Gluetun container's network namespace, all four authenticated control routes returning 200, VPN and DNS running, and unauthenticated requests returning 401. qBittorrent's listening port matched Gluetun's forwarded-port file; UPnP and random port selection remained disabled. Homarr's download query and VPN summary both succeeded. The VPN widget is on Infrastructure. The VPN address, full settings response and credentials were not captured.

I created no snapshot or backup. Temporary API-key and service-credential staging files were overwritten and removed from the source hosts, transfer container and Ubuntu-dev after verification. Homarr retains its encrypted integration credentials; the original service credentials remain in their existing protected configuration.
