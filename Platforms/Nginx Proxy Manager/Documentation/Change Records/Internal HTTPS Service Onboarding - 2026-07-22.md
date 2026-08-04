# Internal HTTPS Service Onboarding

**Created:** 2026-07-22  
**Last updated:** 2026-07-25

**Date:** 2026-07-22  
**Status:** Complete; authenticated application and VPN-client acceptance closed 2026-07-25

## Scope

I added 19 internal service names behind Nginx Proxy Manager. UniFi resolves each name to `192.168.85.2`; NPM forwards it to the existing web listener and presents the existing Let's Encrypt wildcard certificate. I kept NPM administration at `http://192.168.85.2:81`, left direct IP-and-port access available, made no public DNS records, & added no WAN ingress.

Backend-only databases, Redis, `guacd`, FlareSolverr, exporters, Wazuh agent ports, Splunk HEC/syslog/management, Forgejo SSH, & Syncthing transfer ports remain outside NPM.

## Starting State

- NPM 2.15.1 was healthy on `docker-network` with one existing NetBird proxy host.
- Certificate ID 1 covered `*.alphasecunited.com` and `alphasecunited.com` and expired on 2026-10-08.
- UniFi held only the existing NetBird local A record for NPM.
- The 19 applications were reachable by their existing IP-and-port paths.
- Syncthing's server GUI listened only on loopback.
- Grafana's Compose file still contained a bootstrap administrator password value.

## Decisions

- I used direct names such as `jellyfin.alphasecunited.com` because the existing wildcard certificate covers one label beneath the base domain.
- I assigned WebSocket support to every host. That keeps the shared baseline simple and preserves the applications that need upgraded connections.
- I kept HSTS disabled. Force SSL provides the required redirect without making rollback dependent on a cached HSTS policy.
- I used HTTPS upstreams only for Portainer 9443, Wazuh 443, & Splunk 8000. All other NPM-to-application connections use HTTP on the internal network.
- I left each application's own authentication in place. I added no NPM access list to Prometheus or the dashboard because the approved scope didn't call for one.

## Step 1: Capture Recovery Points

I captured the mutable NPM, Docker Main, Media Stack, Ansible, & security-monitoring configuration before changing it.

| Target | Recovery point | SHA-256 or note |
|---|---|---|
| NPM | `/opt/docker/nginx-proxy-manager/backups/internal-https-2026-07-22-prechange/npm-state.tar.gz` | `6967c6dd7cd76d34a7a3abdb4156dfe4e84191f21c8258d466c6abd7278b7cec` |
| Docker Main | `/opt/docker/backups/internal-https-2026-07-22-prechange/docker-main-configs.tar.gz` | `8dc6e361375aa7f93760a70cb7c26aee97c0ecfe95bc35be61390718563bbadb` |
| Media Stack | `/var/lib/vz/dump/internal-https-2026-07-22-prechange/media-01-configs.tar.gz` | `97114cea42417ef24eff75f00cb43db44634d4a896688cdba8b659cddbfa88e7` |
| Ansible | `/var/lib/vz/dump/internal-https-2026-07-22-prechange/ansible-01-configs.tar.gz` | `85cd68768ed57f47c0d60fd0177e3a82d1590ccb66493baf24778c35d53dfb26` |
| Security monitoring | `/home/dkadi/backups/internal-https-2026-07-22-prechange/security-monitoring-compose-sanitized.tar.gz` | Sanitized Compose backup; no password retained |

I didn't change Splunk configuration, so I kept its current service state as the rollback baseline instead of bypassing permissions to archive unrelated files. The NPM recovery point included the SQLite database, generated hosts, ACME state, & certificate files needed to restore the proxy layer.

Evidence: [Step 1 recovery-point verification](../../Evidence/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22/Logs/S01-Recovery-Points-2026-07-22.md). The exact creation commands weren't retained outside the task transcript; the log records the verified artifacts and the permission failures without reconstructing commands.

I deleted all six project-created archives after implementation at the owner's request. The five named recovery points above and the 423-byte `security-ui-configs.tar.gz` archive are no longer available. [Step 6](../../Evidence/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22/Logs/S06-Backup-Removal-2026-07-22.md) records the exact deletion commands and absence checks.

## Step 2: Apply Backend Compatibility Settings

I made only the application changes needed for the new names:

- Jellyfin now advertises `https://jellyfin.alphasecunited.com` and trusts NPM address `192.168.85.2` as a proxy.
- qBittorrent accepts `qbittorrent.alphasecunited.com`, internal Docker hostname `gluetun`, & direct address `192.168.40.42` as WebUI server domains.
- Semaphore's `web_host` uses `https://semaphore.alphasecunited.com`.
- Forgejo's `DOMAIN` and `ROOT_URL` use the new HTTPS host. `SSH_DOMAIN` remains `192.168.40.35`.
- Grafana's domain and root URL use `https://grafana.alphasecunited.com` while its container listener stays HTTP.
- Prometheus starts with `--web.external-url=https://prometheus.alphasecunited.com`.
- Syncthing's server GUI now binds on `0.0.0.0:8384` so NPM can reach it. Its synchronization listeners and peer paths are unchanged.
- I removed Grafana's bootstrap administrator password from Compose, rotated the administrator password, & verified an authenticated request. The linked [Grafana incident report](../../../../Security/Incidents/Grafana/Plaintext%20Administrator%20Credential%20-%202026-07-22.md) records the exposure boundary and corrective actions without retaining the credential.

Recreating the Media Stack pulled the current floating Gluetun and qBittorrent images because that Compose project intentionally uses `pull_policy: always`. Both containers returned running, Jellyfin returned `Healthy`, and qBittorrent's WebUI answered afterward.

That image replacement was an unplanned consequence of applying the Compose change, not a requested application upgrade. The former floating image digests weren't recorded by Compose, and the project-created pre-change archive was later deleted at the owner's request. I accepted the running replacements only after the media containers and proxy paths passed health checks.

The first qBittorrent domain value contained only the NPM hostname. That made the proxy route pass while qBittorrent rejected Sonarr and Radarr requests carrying `Host: gluetun:8080` with HTTP `401`. At 20:49 EDT I added `gluetun` and `192.168.40.42` without disabling Host-header validation. Both Arr saved-client tests then returned HTTP `200`; the [troubleshooting record](../../../Media%20Stack/Documentation/Troubleshooting/qBittorrent%20Host%20Validation%20Blocked%20Arr%20Clients%20-%202026-07-22.md) holds the reproduction, root cause, correction, & verification.

Evidence: [Step 2 backend compatibility verification](../../Evidence/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22/Logs/S02-Backend-Compatibility-Verification-2026-07-22.md). The fresh readback records exact verification commands and outputs; the original edit commands remain only in the task transcript.

## Step 3: Add UniFi DNS and Firewall State

I added 19 enabled local A records with TTL 300. Each direct service name beneath `alphasecunited.com` resolves to `192.168.85.2`. The existing NetBird record remained unchanged.

I previewed the firewall changes before application, then added these five enabled, logged TCP policies from exact source `192.168.85.2`:

| Policy | Destination | Ports | Policy ID |
|---|---|---|---|
| Allow NPM to media-01 web UIs | `192.168.40.42` | 5055, 7878, 8080, 8096, 8989, 9696 | `6a60fd2c2d027bb05525a86d` |
| Allow NPM to ansible-01 Semaphore | `192.168.40.36` | 3000 | `6a60fd2c2d027bb05525a870` |
| Allow NPM to docker-main web UIs | `192.168.40.35` | 2283, 3000, 3001, 6060, 8080, 8090, 8384, 9443 | `6a60fd2c2d027bb05525a873` |
| Allow NPM to security-01 web UIs | `192.168.72.2` | 443, 3000, 9090 | `6a60fd2c2d027bb05525a876` |
| Allow NPM to splunk-siem web UI | `192.168.72.3` | 8000 | `6a60fd2c2d027bb05525a879` |

The policies allow only NPM to the listed web listeners. They don't expose backend databases, monitoring exporters, agent enrollment, SSH, HEC, or syslog ports.

Evidence: [Step 3 UniFi readback](../../Evidence/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22/Logs/S03-UniFi-Readback-2026-07-22.md).

## Step 4: Create the NPM Proxy Hosts

I created the 19 hosts listed in the [proxy-host inventory](../../Configuration/internal-proxy-hosts.md). All use certificate ID 1 with Force SSL, HTTP/2, Block Common Exploits, WebSocket support, & no HSTS. The existing NetBird host is still ID 1 and wasn't edited.

Immich uses this extra Nginx configuration:

```nginx
client_max_body_size 50000M;
proxy_request_buffering off;
client_body_buffer_size 1024k;
proxy_read_timeout 600s;
proxy_send_timeout 600s;
send_timeout 600s;
```

The final NPM table shows every new host Online. The retained inventory is split into three viewport captures so every row stays readable: [top](../../Evidence/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22/Screenshots/S04A-NPM-Proxy-Hosts-2026-07-22.png), [middle](../../Evidence/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22/Screenshots/S04B-NPM-Proxy-Hosts-2026-07-22.png), & [bottom](../../Evidence/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22/Screenshots/S04C-NPM-Proxy-Hosts-2026-07-22.png). Browser screenshots don't render the mouse pointer, so no cursor appears. The [Step 4 NPM state readback](../../Evidence/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22/Logs/S04-NPM-State-Readback-2026-07-22.md) records the textual before state, database query, final controls, & Immich snippet. No pre-change browser screenshot was retained.

## Step 5: Verify the Result

I verified the complete route set from an Internal-zone Windows client:

- All 19 UniFi A queries returned `192.168.85.2`.
- All 19 HTTP requests returned 301 and redirected to HTTPS.
- All 19 HTTPS requests returned an application response: 200, 302, 303, or 307. None returned 502 or 504.
- Every host presented the same `CN=*.alphasecunited.com` certificate, with the same thumbprint prefix and 2026-10-08 expiry. Normal certificate validation succeeded.
- Cloudflare DNS-over-HTTPS returned NXDOMAIN (`Rcode 3`) for all 19 public A queries.
- UniFi reported zero port-forward rules, so TCP 80 and 443 on `192.168.85.2` have no WAN NAT path.
- Jellyfin `/health`, Immich `/api/server/ping`, Portainer `/api/status`, Syncthing `/rest/noauth/health`, Grafana `/api/health`, & Prometheus `/-/healthy` returned HTTP 200.
- Semaphore, Termix, & Splunk login pages returned HTTP 200 through their new names. Forgejo's public API rejected an unauthenticated version request with 403, while its web root returned HTTP 200.
- NPM passed `nginx -t`. A controlled container restart reached `running healthy`; all 19 HTTPS routes still answered afterward.
- NPM's recent proxy access logs contained zero 502 or 504 responses.

I didn't use application credentials to create permanent test media, upload a photo, open an SSH terminal, run a Semaphore job, or execute a Splunk ES search. Existing application authentication remains the control for those actions. The plan's authenticated acceptance checks stayed open after this session instead of being inferred from route health; I ran them on 2026-07-25.

I also couldn't originate a test from an actual VPN client in this session. The UniFi VPN-to-Access and VPN-to-Internal policies are enabled, but policy state isn't a substitute for a client-path test. I ran that client test on 2026-07-25.

Evidence: [Step 5 route and restart verification](../../Evidence/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22/Logs/S05-Route-and-Restart-Verification-2026-07-22.md).

The local evidence index is [Evidence-Index.md](../../Evidence/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22/Evidence-Index.md). Raw evidence stays local under the repository-wide evidence policy.

## Resulting Configuration

- NPM has 20 enabled proxy hosts: 19 new internal application hosts plus the unchanged NetBird host.
- UniFi has 20 local A records for NPM: the 19 new names plus the unchanged NetBird name.
- Five narrow UniFi policies permit NPM to the listed web destinations and ports.
- The NPM administrator remains available only by `http://192.168.85.2:81`.
- Direct IP-and-port access remains available as the immediate rollback path.
- No public A record or UniFi port forward exists for the 19 new names.

## Rollback Points

For one application, I can disable or delete only its NPM proxy host and UniFi A record, then keep using its direct IP-and-port path. Versioned reference configuration remains available for the backend compatibility settings.

For the whole change, I disable the five new firewall policies and remove the 19 UniFi A records. Direct IP-and-port paths remain available. The project-created NPM and backend archives were deleted on 2026-07-22, so rollback can't rely on those files. I don't delete the wildcard certificate while NetBird still uses it.

## Acceptance Closed 2026-07-25

The infrastructure work finished on 2026-07-22. I ran the remaining acceptance checks from my own authenticated sessions and a connected VPN client, and closed them on 2026-07-25:

- from an actual VPN client, resolve one name in each backend zone, open HTTPS, & verify the wildcard certificate;
- play media in Jellyfin;
- upload a test item through Immich;
- open a Termix terminal session;
- run a safe Semaphore task and observe live output;
- verify Grafana Live;
- confirm Syncthing remains connected and synchronized while using the HTTPS GUI;
- run a read-only Splunk ES search.

All eight passed. I kept no screenshot or transcript from that pass, so the closure evidence is my confirmation of the observed behavior rather than a retained capture. Nothing on this change remains open.
