# Internal Proxy Host Inventory

**Created:** 2026-07-22  
**Last updated:** 2026-11-12

On 2026-11-12 I deleted NetBird's host 1, `netbird.alphasecunited.com`, when I [retired NetBird](../../../Archive/Platforms/Netbird/Documentation/Change%20Records/Retirement%20-%202026-11-12.md). The active host count is 28, the rows below, and the database holds 14 soft-deleted rows.

On 2026-11-11 I added hosts 39, 40 and 41 for the E2B Embed trial on `e2b-01`, with a new certificate 3, `*.e2b.alphasecunited.com` and `e2b.alphasecunited.com`, and later host 42, the Desktop viewer. The active host count is 29: the 28 rows below plus NetBird (ID 1). [Embed Trial Deployment](../../E2B/Documentation/Change%20Records/Embed%20Trial%20Deployment%20-%202026-11-11.md).

On 2026-11-02 I added host 38, `*.executor.apps.alphasecunited.com`, for Executor 2's app pages, with its own certificate 2. The active host count is 25: the 24 rows below plus NetBird (ID 1). The database holds 38 rows, 13 of them soft-deleted. UniFi local DNS has no wildcard, so each app page has its own A record: [app page domain](../../Executor/Documentation/Change%20Records/App%20Page%20Domain%20-%202026-11-02.md).

On 2026-11-01 I deleted Homarr's host 34, `dashboard.alphasecunited.com`, when I [retired Homarr](../../../Archive/Platforms/Homarr/Documentation/Change%20Records/Retirement%20-%202026-11-01.md). The active host count is 24: the 23 rows below plus NetBird (ID 1). The database holds 37 rows, 13 of them soft-deleted. UniFi holds 24 local A records pointing at `192.168.85.2`, one per live host.

On 2026-10-31 I replaced Executor 1's host 27, `mcp.alphasecunited.com`, with host 37, `executor.alphasecunited.com`, for Executor 2. The active host count stayed at 25: the 24 rows below plus NetBird (ID 1). On 2026-10-05 I added Sure as host 36. On 2026-09-27 I added Homarr as host 34, then retired WUD host 35. [WUD retirement](../../Prometheus/Documentation/Change%20Records/WUD%20Retirement%20-%202026-09-27.md).

Soft-deleted IDs: 11 termix, 12 dashboard, 14 portainer, 16 syncthing, 21 kasm, 23 kasm, 24 games, 25 wings, 27 mcp, 30 dockge, 33 weebarr, 34 dashboard (Homarr), 35 wud.

Every row except host 38 uses certificate ID 1, Force SSL, HTTP/2, Block Common Exploits, and WebSocket support. HSTS remains disabled. NPM's `Public` access-list label means no NPM access list is assigned; it doesn't mean the name exists in public DNS or has WAN ingress.

| ID | Service name | Upstream | Scheme | Notes |
|---|---|---|---|---|
| 2 | `jellyfin.alphasecunited.com` | `192.168.40.42:8096` | HTTP | Jellyfin trusts `192.168.85.2` and advertises this HTTPS URL. |
| 3 | `seerr.alphasecunited.com` | `192.168.40.42:5055` | HTTP | WebSockets enabled. |
| 4 | `sonarr.alphasecunited.com` | `192.168.40.42:8989` | HTTP | Direct IP access remains available. |
| 5 | `radarr.alphasecunited.com` | `192.168.40.42:7878` | HTTP | Direct IP access remains available. |
| 6 | `prowlarr.alphasecunited.com` | `192.168.40.42:9696` | HTTP | Direct IP access remains available. |
| 7 | `qbittorrent.alphasecunited.com` | `192.168.40.42:8080` | HTTP | qBittorrent allows the NPM hostname, Arr hostname `gluetun`, and direct address `192.168.40.42` without disabling Host-header validation. |
| 8 | `semaphore.alphasecunited.com` | `192.168.40.36:3000` | HTTP | Semaphore advertises this HTTPS web host. |
| 9 | `immich.alphasecunited.com` | `192.168.40.35:2283` | HTTP | Request buffering is off; body limit is 50,000 MiB; proxy read, proxy send, and response-send timeouts are 600 seconds. |
| 10 | `booklore.alphasecunited.com` | `192.168.40.35:6060` | HTTP | BookOrbit v3.1.0 replaced BookLore on 2026-09-28; address and upstream unchanged. |
| 36 | `sure.alphasecunited.com` | `192.168.40.35:3005` | HTTP | Sure 0.7.5-hotfix.1, added 2026-10-05; settings copied from host 34. |
| 13 | `forgejo.alphasecunited.com` | `192.168.40.35:3000` | HTTP | `ROOT_URL` uses HTTPS; SSH cloning stays on `192.168.40.35`. |
| 31 | `dockhand.alphasecunited.com` | `192.168.40.35:3003` | HTTP | Dockhand, proxy host 31. HTTPS login and Hawser WebSockets verified; buffering off, read/send timeouts 3,600 seconds. |
| 15 | `peanut.alphasecunited.com` | `192.168.73.2:8090` | HTTP | Existing application authentication remains in place. |
| 17 | `wazuh.alphasecunited.com` | `192.168.72.2:443` | HTTPS | NPM connects to Wazuh's existing HTTPS listener. |
| 18 | `grafana.alphasecunited.com` | `192.168.73.2:3000` | HTTP | Grafana's domain and root URL use the HTTPS name. |
| 19 | `prometheus.alphasecunited.com` | `192.168.73.2:9090` | HTTP | Prometheus starts with this HTTPS external URL. No added NPM authentication. |
| 20 | `splunk.alphasecunited.com` | `192.168.72.3:8000` | HTTPS | NPM connects to Splunk Web's existing HTTPS listener. HEC, syslog, and management ports remain direct backend services. |
| 22 | `ts3-manager.alphasecunited.com` | `192.168.80.118:9000` | HTTP | TS3 Manager keeps its existing application path; TeamSpeak voice, ServerQuery, file-transfer, and Playit ports remain outside NPM. |
| 26 | `aiproxy.alphasecunited.com` | `192.168.40.35:8317` | HTTP | CLI Proxy API. Request and response buffering and proxy caching are off; proxy read, proxy send, and response-send timeouts are 3,600 seconds. I repointed the upstream from `ubuntu-dev` to `docker-main` on 2026-08-19; five provider auth files and clients are loaded. |
| 37 | `executor.alphasecunited.com` | `192.168.40.39:4400` | HTTP | Executor 2 on `docker-blue`, added 2026-10-31 with the settings and advanced configuration of host 27, which it replaced. Proxy buffering and caching are off; proxy read, proxy send, and response-send timeouts are 3,600 seconds. The owner account is claimed. Since 2026-11-02 its advanced configuration has its own `location /` that removes `Accept-Encoding` and uses `sub_filter` to insert a `URL.parse` polyfill into HTML for iPadOS 17: [Safari 17 URL.parse polyfill](../../Executor/Documentation/Change%20Records/Safari%2017%20URL.parse%20Polyfill%20-%202026-11-02.md). |
| 38 | `*.executor.apps.alphasecunited.com` | `192.168.40.39:4400` | HTTP | Executor 2 app pages, added 2026-11-02 with host 37's settings and advanced configuration. Uses certificate 2, `*.executor.apps.alphasecunited.com`, Let's Encrypt DNS-01 through Cloudflare, expiring 2027-01-31. |
| 39 | `e2b.alphasecunited.com` | `192.168.80.30:3001` | HTTP | E2B dashboard on `e2b-01`, added 2026-11-11. Certificate 3, Force SSL, HTTP/2, Block Common Exploits, WebSocket support, HSTS off. Proxy buffering, caching and request buffering off; 3,600-second proxy read, proxy send and send timeouts; `client_max_body_size 1024m`. |
| 40 | `api.e2b.alphasecunited.com` | `192.168.80.30:3000` | HTTP | E2B API on `e2b-01`, added 2026-11-11, same settings as host 39. |
| 41 | `sandbox.e2b.alphasecunited.com` | `192.168.80.30:3002` | HTTP | E2B client-proxy (sandbox traffic, routed on the `E2b-Sandbox-Id` and `E2b-Sandbox-Port` headers) on `e2b-01`, added 2026-11-11, same settings as host 39. A 70-second streaming command passed through it. |
| 42 | `desktop.e2b.alphasecunited.com` | `192.168.80.30:3002` | HTTP | E2B Desktop viewer, added 2026-11-11. Certificate 3, same flags as host 39. Its advanced configuration ([npm-desktop-viewer.conf](../../E2B/Configuration/npm-desktop-viewer.conf)) routes `/<sandbox id>/...` to that sandbox's port 6080 by setting `E2b-Sandbox-Id`, `E2b-Sandbox-Port` and `Host: sandbox.e2b.alphasecunited.com`, with WebSocket upgrades. |
| 28 | `openwebui.alphasecunited.com` | `192.168.40.35:3002` | HTTP | Authenticated Open WebUI frontend for Ollama. Its HTTPS root is included in the Prometheus blackbox target set. |
| 29 | `mesh.alphasecunited.com` | `192.168.40.39:443` | HTTPS | MeshCentral on `docker-blue`, proxy host 29, added 2026-09-13. Forwards over HTTPS so the hop to the backend stays encrypted. WebSocket upgrade is on, which both the browser and the agents need. Proxy buffering and caching are off; proxy read, proxy send, and response-send timeouts are 3,600 seconds. |
| 32 | `appportal.alphasecunited.com` | `192.168.40.35:3004` | HTTP | App Portal on `docker-main`, proxy host 32, added 2026-09-19. Serves the desktop client's API, so it carries a device bearer token and exists to keep that token off the wire in the clear. WebSocket upgrade is off; the client polls. |

NPM administration stays at `http://192.168.85.2:81` without a domain name.

The implementation and rollback record is [Internal HTTPS Service Onboarding - 2026-07-22](../Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

I replaced host 27 with host 37 on 2026-10-31: [Executor 2 Migration - 2026-10-31](../../Executor/Documentation/Change%20Records/Executor%202%20Migration%20-%202026-10-31.md).

I added App Portal as proxy host 32 on 2026-09-19: [Internal HTTPS, ObiPC Enrollment and the First Self-Update - 2026-09-19](../../App%20Portal/Documentation/Change%20Records/Internal%20HTTPS%2C%20ObiPC%20Enrollment%20and%20the%20First%20Self-Update%20-%202026-09-19.md).

I added Open WebUI as proxy host 28 on 2026-09-05: [Open WebUI Internal HTTPS - 2026-09-05](../Documentation/Change%20Records/Open%20WebUI%20Internal%20HTTPS%20-%202026-09-05.md).

I repointed Grafana and Prometheus to `monitor-01` on 2026-07-26 and left Wazuh on `security-01`: [Monitoring Relocation to monitor-01 - 2026-07-26](../../Prometheus/Documentation/Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md).

I added WUD HTTPS for the [Homarr integrations](../../../Archive/Platforms/Homarr/Documentation/Change%20Records/Media%20and%20Infrastructure%20Integrations%20-%202026-09-27.md).
