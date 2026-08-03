# Nginx Proxy Manager TODO

**Created:** 2026-07-11  
**Last updated:** 2026-07-28

NPM 2.15.1 is healthy, its administrator is initialized, and the NetBird HTTPS host, automated renewal path, and bounded logging are verified. This record preserves the completed publication and readiness work; I track no further hardening after my 2026-07-12 descope decision. Completed deployment details are recorded in [Deployment.md](Deployment.md).

## Complete NetBird Publication

- [x] Configure Cloudflare DNS-01 validation for the NPM certificate.
- [x] Request the `*.alphasecunited.com` and `alphasecunited.com` DNS-01 certificate.
- [x] Assign the certificate, enable Force SSL, and enable HTTP/2.
- [x] Verify certificate presentation and the authenticated NetBird dashboard over HTTPS.
- [x] Enroll the first NetBird peer and verify VPN traffic plus peer-dependent API, OAuth2, WebSocket, signal, management, and gRPC behavior. Completed 2026-07-12; see the NetBird [change record](../../Netbird/Documentation/Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md).
- [x] Verify the non-interactive Cloudflare DNS-01 renewal path with a successful Let's Encrypt staging dry-run and identify NPM's hourly renewal scheduler. Completed 2026-07-12; see the NetBird [change record](../../Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).

## Operational Readiness

- [x] Perform NPM and NetBird Compose restart validation.
- [x] Configure and verify bounded `json-file` logging (`10m` × `3`) for `nginx-proxy-manager`. Completed 2026-07-12; see the NetBird [change record](../../Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).

Operational status is complete. I intentionally descoped further hardening on 2026-07-12; NPM stays internal-only with no WAN ingress and intentionally tracks `latest`.

## Internal HTTPS Service Onboarding

- [x] 2026-07-22: Added 19 UniFi local A records for internal application names, all pointing to `192.168.85.2`.
- [x] 2026-07-22: Added five narrow NPM-to-backend firewall policies covering only the approved web listeners.
- [x] 2026-07-22: Added all 19 NPM proxy hosts with the wildcard certificate, Force SSL, HTTP/2, Block Common Exploits, & WebSocket support.
- [x] 2026-07-22: Applied the required Jellyfin, qBittorrent, Semaphore, Forgejo, Grafana, Prometheus, Immich, & Syncthing compatibility settings.
- [x] 2026-07-22: Verified Internal-zone DNS, public NXDOMAIN, zero UniFi port forwards, HTTP redirects, certificate presentation, application responses, `nginx -t`, zero 502/504 responses, & controlled restart recovery. See the [change record](Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).
- [x] 2026-07-25: Verified DNS, HTTPS, & certificate presentation from an actual VPN client.
- [x] 2026-07-25: Ran the authenticated Jellyfin playback, Immich upload, Termix session, Semaphore live-output, Grafana Live, Syncthing synchronization, & Splunk ES search acceptance checks. I kept no capture from this pass, so the closure evidence is my own confirmation that each workflow worked.

Internal HTTPS onboarding is closed. NPM now has no open items.

## TS3 Manager Internal HTTPS

- [x] 2026-07-28: Added one TTL-300 UniFi A record for `ts3-manager.alphasecunited.com` pointing to `192.168.85.2`.
- [x] 2026-07-28: Added one logged policy permitting only NPM at `192.168.85.2` to reach `alpha-prod-01` at `192.168.80.118:9000`.
- [x] 2026-07-28: Added NPM proxy host ID 22 with certificate ID 1, Force SSL, HTTP/2, Block Common Exploits, & WebSocket support.
- [x] 2026-07-28: Completed restart recovery, 46-target blackbox monitoring, documentation, final route validation, & deletion of every backup and temporary deployment file created by the change.

## Kasm Workspaces Internal HTTPS

- [x] 2026-07-28: Added `kasm.alphasecunited.com` as NPM proxy host ID 23 with an HTTPS upstream, certificate ID 1, Force SSL, HTTP/2, Block Common Exploits, & WebSocket support.
- [x] 2026-07-28: Added one TTL-300 UniFi A record and one logged policy permitting only `192.168.85.2` to reach `192.168.78.10:443`.
- [x] 2026-07-28: Narrowed the LAB-MGMT-to-Access block from `ALL` to `NEW, INVALID` after a packet capture proved it dropped Kasm's SYN-ACK.
- [x] 2026-07-28: Added the twentieth NPM blackbox probe, verified all 48 scrape targets `up`, & verified `probe_success=1` for all 20 active URLs.
