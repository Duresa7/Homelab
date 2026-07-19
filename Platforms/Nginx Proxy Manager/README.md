# Nginx Proxy Manager

**Created:** 2026-07-11  
**Last updated:** 2026-07-18

Nginx Proxy Manager (NPM) is my reverse-proxy and certificate-management service on the dedicated `docker-network` LXC. Its first consumer is NetBird, whose dashboard, API, WebSocket, and gRPC paths share the HTTPS host `REDACTED_CUSTOM_DOMAIN_016`.

## Current State

| Item | Current value |
|---|---|
| Deployment status | Runtime healthy; NetBird HTTPS proxy, automated renewal path, routed VPN traffic, and bounded logging verified |
| Compute | Galaxy CT 107 `docker-network`, Debian 13, `192.168.85.2` |
| NPM release | 2.15.1 |
| Live path | `/opt/docker/nginx-proxy-manager` |
| Container | `nginx-proxy-manager` |
| Guest bindings | TCP 80, 81, and 443 |
| Docker network | External `proxy`, `172.31.85.0/24` |
| Fixed container address | `172.31.85.10` |
| Persistent data | Live `data/` and `letsencrypt/` bind mounts |
| NetBird certificate | Let's Encrypt wildcard/apex certificate; expires `2026-10-08 23:49:46 UTC` |
| NetBird TLS policy | Certificate assigned; Force SSL and HTTP/2 enabled |

The NPM health check is passing and the administrative UI returns HTTP `200` at `http://192.168.85.2:81`. The first-run administrator account is initialized. The NetBird proxy host is saved and Online, its advanced configuration passes `nginx -t`, and its Cloudflare DNS-01 certificate is assigned with Force SSL and HTTP/2 enabled. The HTTPS client path, authenticated dashboard, first-peer VPN traffic, controlled Compose restart, non-interactive staging renewal, and bounded `json-file` logging (`10m` × `3`) are all verified. I intentionally descoped further hardening on 2026-07-12.

## Records

- [Deployment record](Documentation/Deployment.md)
- [Operations runbook](Documentation/Runbook.md)
- [Troubleshooting log](Documentation/Troubleshooting-Log.md)
- [Platform backlog](Documentation/TODO.md)
- [Configuration reference](Configuration/README.md)
- [NetBird/NPM operational follow-ups and hardening descope (2026-07-12)](../Netbird/Documentation/Change%20Records/NetBird-NPM%20Operational%20Follow-ups%20and%20Hardening%20Descope%20-%202026-07-12.md)
- [NetBird platform](../Netbird/README.md)

## Layout

- `Documentation/`: deployment history, operating procedure, troubleshooting, and remaining work
- `Configuration/`: secret-free Compose reference and intended NetBird advanced routes

The combined deployment evidence stays with NetBird, the primary platform owner for this bounded job, rather than being copied into a second evidence tree.

## Security Boundaries

- The NPM database, account credential, private keys, ACME account data, and Cloudflare API token stay out of this repository.
- The live NPM SQLite database is owner-only mode `0600`; its secret-bearing contents are never captured in evidence.
- The zone-scoped Cloudflare DNS Write token lives in 1Password as `REDACTED_1PASSWORD_ITEM_TITLE_002`; only its non-secret name and scope are documented here.
- I retrieve Cloudflare DNS credentials from 1Password and enter them without letting them appear in screenshots, transcripts, or visible shell arguments.
- NPM holds fixed address `172.31.85.10`; NetBird trusts only `172.31.85.10/32` as its HTTP proxy.
