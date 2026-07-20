# NetBird TODO

**Created:** 2026-07-11  
**Last updated:** 2026-07-20

The NetBird control plane, HTTPS publication, authenticated administrator dashboard, Compose-level restart recovery, first peers, routed VPN path into Access-A, automated certificate renewal path, and bounded Docker logging are all verified. I track no further hardening after my 2026-07-12 descope decision. Completed implementation is recorded in [Deployment.md](Deployment.md) and the [Change Records](Change%20Records/).

## Completed Deployment

- [x] Deploy Debian 13 LXC 107 `docker-network` on Access-A/VLAN 85 with HA, key-only SSH, Docker Engine, and Compose.
- [x] Deploy NetBird 0.74.3 and Nginx Proxy Manager 2.15.1 under `/opt/docker`.
- [x] Configure least-privilege UniFi egress, internal DNS, Cloudflare DNS-01 TLS, Force SSL, HTTP/2, and the authenticated dashboard.
- [x] Validate controlled Compose restarts, remove deployment leftovers, and restrict configuration file permissions.

## First Peer and VPN Path

Completed 2026-07-12; see [NetBird First Peer and Routed VPN Path - 2026-07-12](Change%20Records/NetBird%20First%20Peer%20and%20Routed%20VPN%20Path%20-%202026-07-12.md).

- [x] Enroll the first NetBird peers and confirm they reach the control plane through `https://<YOUR_NETBIRD_DOMAIN>`.
- [x] Exercise the live WireGuard data path with real peers (direct peer-to-peer tunnel confirmed), not configuration-only probes.
- [x] Confirm the VPN-client path into Access-A and document the owning route (`<YOUR_ORG_NAME>`-Access network, `docker-network` routing peer) and masquerade/firewall behavior.

## Operational Follow-ups

- [x] Verify the non-interactive Cloudflare DNS-01 renewal path with a successful Let's Encrypt staging dry-run and identify NPM's hourly renewal scheduler. Completed 2026-07-12; see [NetBird/NPM Operational Follow-ups and Hardening Descope - 2026-07-12](Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).
- [x] Apply and verify bounded `json-file` logging (`10m` × `3`) for `netbird-server` and `netbird-dashboard`.

Operational status is complete. I intentionally descoped further hardening on 2026-07-12; the stack stays internal-only with no WAN ingress and intentionally tracks `latest`. See the [descope change record](Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md) for the complete decision record.
