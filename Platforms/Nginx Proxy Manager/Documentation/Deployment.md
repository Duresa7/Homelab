# Nginx Proxy Manager Deployment

**Created:** 2026-07-11  
**Last updated:** 2026-07-18

**Implementation started:** 2026-07-10  
**Status:** Operational; NPM runtime, certificate assignment and renewal path, NetBird HTTPS/VPN traffic, Compose restart validation, and bounded logging are complete

## Scope

Deploy Nginx Proxy Manager on CT 107 `docker-network` using my standard `/opt/docker/<service>` Compose layout. NPM provides the shared HTTP/HTTPS entry point and certificate lifecycle for NetBird while talking to the NetBird containers over a dedicated external Docker network.

NetBird is the primary owner of the combined job. I keep the combined step evidence with the NetBird platform.

## Starting State

- CT 107 and Docker did not exist before this bounded deployment.
- No Nginx Proxy Manager instance or shared `proxy` Docker network existed on the new guest.
- No Cloudflare DNS-01 certificate or proxy host existed for `REDACTED_CUSTOM_DOMAIN_016`.

## Implementation

1. I installed Docker Engine 29.6.1 and Docker Compose 5.3.1 on Debian 13.
2. I created the external Docker network `proxy` with subnet `172.31.85.0/24`.
3. I created the Compose project at `/opt/docker/nginx-proxy-manager`.
4. I deployed `jc21/nginx-proxy-manager:latest` with fixed address `172.31.85.10` and restart policy `unless-stopped`.
5. I published TCP ports 80, 81, and 443 on guest `192.168.85.2`.
6. I mounted persistent `data/` and `letsencrypt/` directories into the container.
7. The application reported version 2.15.1, passed its built-in health check, and returned HTTP `200` on ports 80 and 81.
8. I completed the first-run administrator setup through the authenticated UI without placing the password in evidence.
9. I saved the NetBird proxy host; it reported Online with upstream `http://netbird-dashboard:80`, Block Common Exploits, and WebSocket Support enabled.
10. I applied the 1,296-character advanced configuration for API, OAuth2, WebSocket, signal, management, and gRPC routing.
11. `nginx -t` succeeded, and an HTTP Host-header request through NPM returned the NetBird dashboard with status `200`.
12. I created a least-privilege Cloudflare DNS Write token named `REDACTED_1PASSWORD_ITEM_TITLE_002` for `REDACTED_CUSTOM_DOMAIN_001` and stored it in 1Password without retaining its value in Git, screenshots, or transcripts.
13. NPM obtained a Let's Encrypt DNS-01 certificate for `*.REDACTED_CUSTOM_DOMAIN_001` and `REDACTED_CUSTOM_DOMAIN_001`. The certificate expires `2026-10-08 23:49:46 UTC`.
14. I assigned the certificate to `REDACTED_CUSTOM_DOMAIN_016` and enabled Force SSL and HTTP/2. I intentionally left HSTS disabled during the initial deployment.
15. The HTTPS client path presented the expected certificate and loaded the authenticated NetBird dashboard.
16. I restarted the NPM and NetBird Compose projects in a controlled validation. Both stacks returned healthy, the proxy configuration remained valid, and the authenticated HTTPS dashboard remained reachable.

## Resulting Configuration

| Setting | Value |
|---|---|
| Guest | CT 107 `docker-network`, Debian 13 |
| Guest address | `192.168.85.2` |
| Live project | `/opt/docker/nginx-proxy-manager` |
| Verified NPM version | 2.15.1 |
| Published TCP ports | 80, 81, 443 |
| Time zone | `America/New_York` |
| IPv6 in NPM | Disabled |
| Persistence | `./data:/data`, `./letsencrypt:/etc/letsencrypt` |
| Docker network | External `proxy`, `172.31.85.0/24` |
| Fixed address | `172.31.85.10` |
| Restart policy | `unless-stopped` |
| Administrator | Initialized |
| NetBird certificate | Let's Encrypt wildcard/apex certificate; expires `2026-10-08 23:49:46 UTC` |
| Cloudflare credential | Zone-scoped DNS Write token `REDACTED_1PASSWORD_ITEM_TITLE_002`, stored in 1Password |
| NetBird proxy host | Saved and Online; advanced routes, certificate, Force SSL, and HTTP/2 applied |

The checked-in Compose file and NetBird advanced-routing snippet are secret-free references. Runtime data, the SQLite database, private keys, ACME state, and DNS-provider credentials remain outside Git.

## Applied NetBird Integration

The intended proxy host is:

| Field | Current value |
|---|---|
| Domain | `REDACTED_CUSTOM_DOMAIN_016` |
| Scheme | `http` |
| Default upstream | `netbird-dashboard:80` |
| WebSocket support | Enabled |
| Block common exploits | Enabled |
| Advanced routes | `Configuration/netbird-advanced-config.conf` |
| Certificate | Let's Encrypt DNS-01 certificate for `*.REDACTED_CUSTOM_DOMAIN_001` and `REDACTED_CUSTOM_DOMAIN_001`; expires `2026-10-08 23:49:46 UTC` |
| Force SSL | Enabled |
| HTTP/2 | Enabled |

The advanced configuration sends dashboard traffic to `netbird-dashboard` and NetBird API, OAuth2, WebSocket, signal, management, and gRPC paths to `netbird-server`. The HTTPS host is active, and S07 certificate assignment and client-path validation are complete. I validated first-peer enrollment and end-to-end VPN traffic on 2026-07-12.

## Verification Performed

- The NPM container remained `Up (healthy)`.
- The built-in health check returned `healthy`.
- HTTP checks on guest ports 80 and 81 returned `200` after initialization.
- NPM reported application version 2.15.1.
- Docker inspection returned fixed address `172.31.85.10` and restart policy `unless-stopped`.
- NPM resolved `netbird-dashboard` and `netbird-server` over `proxy` and received HTTP `200` from the dashboard and embedded identity provider.
- The NetBird host reports Online, `nginx -t` succeeds, and a Host-header request through NPM returns the dashboard with HTTP `200`.
- I captured the initialized-administrator dashboard without exposing credentials.
- The wildcard/apex certificate was issued through Cloudflare DNS-01, assigned to the NetBird host, and observed with expiry `2026-10-08 23:49:46 UTC`.
- The renewal configuration uses the non-interactive `dns-cloudflare` authenticator, NPM's Node backend checks hourly for certificates within 30 days of expiry, and a Let's Encrypt staging dry-run succeeded for lineage `npm-1` on 2026-07-12.
- Force SSL redirects the client path to HTTPS, HTTP/2 is enabled, and the authenticated NetBird dashboard loads through `https://REDACTED_CUSTOM_DOMAIN_016`.
- After controlled NPM and NetBird Compose restarts, all containers returned healthy and the authenticated HTTPS dashboard remained reachable.
- Docker inspection confirmed bounded `json-file` logging with `max-size=10m` and `max-file=3` on the NPM container.

These results verify the runtime, inter-container path, saved host, certificate assignment and automated renewal path, HTTPS client path, authenticated dashboard, peer-dependent VPN traffic, Compose-level restart recovery, and bounded logging. See the NetBird [operational follow-ups/descope record](../../Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md).

## Rollback and Recovery

- Routine rollback stops the Compose project without deleting `data/` or `letsencrypt/`.
- Preserve the live Compose file, `data/`, and `letsencrypt/` together as protected backup material before an update or migration.
- If an image update fails, restore the previously verified image version or digest and recreate the container against the preserved bind mounts.
- Removing a proxy host or certificate is a separate application-level change; export or document its non-secret settings first and avoid deleting a certificate still used by another host.
- Removing NPM from CT 107 also removes NetBird's intended TLS entry point. Coordinate rollback with the NetBird records.

## Operational Status

No further NPM hardening is tracked. I intentionally descoped the remaining manual or declined items on 2026-07-12; see the NetBird [operational follow-ups/descope record](../../Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md). Recovery guidance above remains reference material. The [troubleshooting log](Troubleshooting-Log.md) retains historical deployment issues, including the stale saved API credential, without making that password-manager record I own personally into platform backlog.
