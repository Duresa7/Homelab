# Nginx Proxy Manager TODO

**Created:** 2026-07-11  
**Last updated:** 2026-07-18

NPM 2.15.1 is healthy, its administrator is initialized, and the NetBird HTTPS host, automated renewal path, and bounded logging are verified. This record preserves the completed publication and readiness work; I track no further hardening after my 2026-07-12 descope decision. Completed deployment details are recorded in [Deployment.md](Deployment.md).

## Complete NetBird Publication

- [x] Store the zone-scoped Cloudflare DNS Write token as `REDACTED_1PASSWORD_ITEM_TITLE_002` in 1Password without retaining its value in Git or evidence.
- [x] Request the `*.REDACTED_CUSTOM_DOMAIN_001` and `REDACTED_CUSTOM_DOMAIN_001` DNS-01 certificate.
- [x] Assign the certificate, enable Force SSL, and enable HTTP/2.
- [x] Verify certificate presentation and the authenticated NetBird dashboard over HTTPS.
- [x] Enroll the first NetBird peer and verify VPN traffic plus peer-dependent API, OAuth2, WebSocket, signal, management, and gRPC behavior. Completed 2026-07-12; see the NetBird [change record](../../Netbird/Documentation/Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md).
- [x] Verify the non-interactive Cloudflare DNS-01 renewal path with a successful Let's Encrypt staging dry-run and identify NPM's hourly renewal scheduler. Completed 2026-07-12; see the NetBird [change record](../../Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).
- [x] Capture S07 certificate, proxy-host, and TLS step evidence.
- [x] Capture S08 authenticated-dashboard step evidence.

## Operational Readiness

- [x] Perform NPM and NetBird Compose restart validation and capture S09 evidence.
- [x] Configure and verify bounded `json-file` logging (`10m` × `3`) for `nginx-proxy-manager`. Completed 2026-07-12; see the NetBird [change record](../../Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).

Operational status is complete. I intentionally descoped further hardening on 2026-07-12; NPM stays internal-only with no WAN ingress and intentionally tracks `latest`.
