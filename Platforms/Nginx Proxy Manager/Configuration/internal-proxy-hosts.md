# Internal Proxy Host Inventory

**Created:** 2026-07-22  
**Last updated:** 2026-08-03

I route 21 enabled internal service names through Nginx Proxy Manager at `192.168.85.2`: the 20 rows below plus NetBird. UniFi holds the matching local A records. I don't publish these names in public DNS.

Every row uses certificate ID 1, Force SSL, HTTP/2, Block Common Exploits, & WebSocket support. HSTS remains disabled. NPM's `Public` access-list label means no NPM access list is assigned; it doesn't mean the name exists in public DNS or has WAN ingress.

| Service name | Upstream | Scheme | Notes |
|---|---|---|---|
| `jellyfin.alphasecunited.com` | `192.168.40.42:8096` | HTTP | Jellyfin trusts `192.168.85.2` and advertises this HTTPS URL. |
| `seerr.alphasecunited.com` | `192.168.40.42:5055` | HTTP | WebSockets enabled. |
| `sonarr.alphasecunited.com` | `192.168.40.42:8989` | HTTP | Direct IP access remains available. |
| `radarr.alphasecunited.com` | `192.168.40.42:7878` | HTTP | Direct IP access remains available. |
| `prowlarr.alphasecunited.com` | `192.168.40.42:9696` | HTTP | Direct IP access remains available. |
| `qbittorrent.alphasecunited.com` | `192.168.40.42:8080` | HTTP | qBittorrent allows the NPM hostname, Arr hostname `gluetun`, & direct address `192.168.40.42` without disabling Host-header validation. |
| `semaphore.alphasecunited.com` | `192.168.40.36:3000` | HTTP | Semaphore advertises this HTTPS web host. |
| `immich.alphasecunited.com` | `192.168.40.35:2283` | HTTP | Request buffering is off; body limit is 50,000 MiB; proxy read, proxy send, & response-send timeouts are 600 seconds. |
| `booklore.alphasecunited.com` | `192.168.40.35:6060` | HTTP | Direct IP access remains available. |
| `dashboard.alphasecunited.com` | `192.168.40.35:3001` | HTTP | No added NPM authentication. |
| `forgejo.alphasecunited.com` | `192.168.40.35:3000` | HTTP | `ROOT_URL` uses HTTPS; SSH cloning stays on `192.168.40.35`. |
| `portainer.alphasecunited.com` | `192.168.40.35:9443` | HTTPS | NPM connects to Portainer's existing HTTPS listener. |
| `peanut.alphasecunited.com` | `192.168.73.2:8090` | HTTP | Existing application authentication remains in place. |
| `syncthing.alphasecunited.com` | `192.168.40.35:8384` | HTTP | The server GUI binds on `0.0.0.0:8384`; synchronization stays on TCP/UDP 22000. |
| `wazuh.alphasecunited.com` | `192.168.72.2:443` | HTTPS | NPM connects to Wazuh's existing HTTPS listener. |
| `grafana.alphasecunited.com` | `192.168.73.2:3000` | HTTP | Grafana's domain & root URL use the HTTPS name. |
| `prometheus.alphasecunited.com` | `192.168.73.2:9090` | HTTP | Prometheus starts with this HTTPS external URL. No added NPM authentication. |
| `splunk.alphasecunited.com` | `192.168.72.3:8000` | HTTPS | NPM connects to Splunk Web's existing HTTPS listener. HEC, syslog, & management ports remain direct backend services. |
| `ts3-manager.alphasecunited.com` | `192.168.80.118:9000` | HTTP | TS3 Manager keeps its existing application path; TeamSpeak voice, ServerQuery, file-transfer, & Playit ports remain outside NPM. |
| `kasm.alphasecunited.com` | `192.168.78.10:443` | HTTPS | NPM connects to Kasm's existing HTTPS listener. SSH, exporters, & all four session lanes remain outside NPM. |

The existing `netbird.alphasecunited.com` host remains unchanged. NPM administration stays at `http://192.168.85.2:81` without a domain name.

The implementation and rollback record is [Internal HTTPS Service Onboarding - 2026-07-22](../Documentation/Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).

I repointed Grafana and Prometheus to `monitor-01` on 2026-07-26 and left Wazuh on `security-01`: [Monitoring Relocation to monitor-01 - 2026-07-26](../../Prometheus/Documentation/Change%20Records/Monitoring%20Relocation%20to%20monitor-01%20-%202026-07-26.md).
