# Nginx Proxy Manager TODO

**Created:** 2026-07-11  
**Last updated:** 2026-09-25

NPM 2.15.1 is healthy, its administrator is initialized, and the NetBird HTTPS host, automated renewal path, and bounded logging are verified. This record preserves the completed publication and readiness work. Completed deployment details are recorded in [Deployment.md](Deployment.md).

## Complete NetBird Publication

- [x] Configure Cloudflare DNS-01 validation for the NPM certificate.
- [x] Request the `*.alphasecunited.com` and `alphasecunited.com` DNS-01 certificate.
- [x] Assign the certificate, enable Force SSL, and enable HTTP/2.
- [x] Verify certificate presentation and the authenticated NetBird dashboard over HTTPS.
- [x] Enroll the first NetBird peer and verify VPN traffic plus peer-dependent API, OAuth2, WebSocket, signal, management, and gRPC behavior. Completed 2026-07-12; see the NetBird [change record](../../Netbird/Documentation/Change%20Records/First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md).
- [x] Verify the non-interactive Cloudflare DNS-01 renewal path with a successful Let's Encrypt staging dry-run and identify NPM's hourly renewal scheduler. Completed 2026-07-12; see the NetBird [change record](../../Netbird/Documentation/Change%20Records/NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).

## Operational Readiness

- [x] Perform NPM and NetBird Compose restart validation.
- [x] Configure and verify bounded `json-file` logging (`10m` × `3`) for `nginx-proxy-manager`. Completed 2026-07-12; see the NetBird [change record](../../Netbird/Documentation/Change%20Records/NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).

Operational status is complete. I intentionally descoped further hardening on 2026-07-12; NPM stays internal-only with no WAN ingress and tracked `latest` until 2026-09-25, when a scheduled Dockhand update left it stopped. It is now pinned to 2.15.1 and excluded from Dockhand updates. [Incident](../../../Security/Incidents/Nginx%20Proxy%20Manager/Scheduled%20Update%20Stranded%20the%20Proxy%20-%202026-09-25.md).

## Manual Upgrades

- [ ] Upgrade to 2.16.0. The image is already pulled on `docker-network` as `latest`. Read the release notes for database migrations, then change the pinned tag in both the live Compose file and Dockhand's imported definition on `docker-main`, run `docker compose up -d` from the host shell rather than from Dockhand, and run the routine health check and the full host sweep.

## Internal HTTPS Service Onboarding

- [x] 2026-07-22: Added 19 UniFi local A records for internal application names, all pointing to `192.168.85.2`.
- [x] 2026-07-22: Added five narrow NPM-to-backend firewall policies covering only the approved web listeners.
- [x] 2026-07-22: Added all 19 NPM proxy hosts with the wildcard certificate, Force SSL, HTTP/2, Block Common Exploits, & WebSocket support.
- [x] 2026-07-22: Applied the required Jellyfin, qBittorrent, Semaphore, Forgejo, Grafana, Prometheus, Immich, & Syncthing compatibility settings.
- [x] 2026-07-22: Verified Internal-zone DNS, public NXDOMAIN, zero UniFi port forwards, HTTP redirects, certificate presentation, application responses, `nginx -t`, zero 502/504 responses, & controlled restart recovery. See the [change record](Change%20Records/Internal%20HTTPS%20Service%20Onboarding%20-%202026-07-22.md).
- [x] 2026-07-25: Verified DNS, HTTPS, & certificate presentation from an actual VPN client.
- [x] 2026-07-25: Ran the authenticated Jellyfin playback, Immich upload, Termix session, Semaphore live-output, Grafana Live, Syncthing synchronization, & Splunk Enterprise Security search acceptance checks. I kept no capture from this pass, so the closure evidence is my own confirmation that each workflow worked.

Internal HTTPS onboarding is closed. NPM now has no open items.

## TS3 Manager Internal HTTPS

- [x] 2026-07-28: Added one TTL-300 UniFi A record for `ts3-manager.alphasecunited.com` pointing to `192.168.85.2`.
- [x] 2026-07-28: Added one logged policy permitting only NPM at `192.168.85.2` to reach `alpha-prod-01` at `192.168.80.118:9000`.
- [x] 2026-07-28: Added NPM proxy host ID 22 with certificate ID 1, Force SSL, HTTP/2, Block Common Exploits, & WebSocket support.
- [x] 2026-07-28: Completed restart recovery, 46-target blackbox monitoring, documentation, final route validation, & deletion of every backup and temporary deployment file created by the change.

## Open WebUI Internal HTTPS

- [x] 2026-09-04: Added the TTL-300 UniFi A record for `openwebui.alphasecunited.com` pointing to `192.168.85.2`.
- [x] 2026-09-04: Verified that Cloudflare's public resolver returns NXDOMAIN for the internal name.
- [x] 2026-09-04: Added TCP/3002 to the narrow policy permitting only NPM to the approved `docker-main` web interfaces and verified the backend health path from `docker-network`.
- [x] 2026-09-04: Repaired the stored NPM administrator credential. The stored value did not authenticate, so I wrote a new bcrypt secret for `<REDACTED_PERSONAL_EMAIL>` directly to `auth.secret` and confirmed `POST /api/tokens` returns 200 with it and 400 without. The credential is now the shared `Account dkadi` password. [Service Login Password Standardization](../../../Operations/Maintenance/Service%20Login%20Password%20Standardization%20-%202026-09-04.md).
- [x] 2026-09-05: Added proxy host 28 forwarding HTTP to `192.168.40.35:3002` with certificate ID 1, Force SSL, HTTP/2, Block Common Exploits, and WebSocket support. HTTP redirects with `301`, HTTPS returns `200`, the wildcard certificate is presented, and the root path is a blackbox target. [Open WebUI Internal HTTPS - 2026-09-05](Change%20Records/Open%20WebUI%20Internal%20HTTPS%20-%202026-09-05.md).

NPM again has no open items.
