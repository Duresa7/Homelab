# Nginx Proxy Manager Configuration

**Created:** 2026-07-11  
**Last updated:** 2026-07-17

The live Compose project is `/opt/docker/nginx-proxy-manager` on `docker-network`. This folder contains only secret-free reference configuration.

## Files

- `docker-compose.yml` defines the NPM service, persistent bind mounts, published ports, bounded `json-file` logging (`10m` × `3`), health check, restart policy, and fixed address `172.31.85.10` on external Docker network `proxy`.
- `netbird-advanced-config.conf` is the applied NPM Advanced snippet for `REDACTED_CUSTOM_DOMAIN_016`. It routes the NetBird API/OAuth2, WebSocket, signal, management, and gRPC paths to `netbird-server:80` while the default proxy host points to `netbird-dashboard:80`.

## Live-State Exclusions

The following live data is intentionally excluded from Git:

- `data/`, including the NPM database, accounts, proxy-host state, and generated Nginx files;
- `letsencrypt/`, including ACME account state, certificates, and private keys;
- Cloudflare API tokens and DNS credential files;
- session tokens, cookies, and administrator credentials.

Use 1Password for approved credential storage. Do not place secret values in visible commands, screenshots, evidence transcripts, or configuration examples.

## Operational Notes

- The external `proxy` network uses subnet `172.31.85.0/24` and must exist before Compose starts.
- NetBird's live `reverseProxy.trustedHTTPProxies` entry must match NPM's fixed address `172.31.85.10/32`.
- The verified runtime is NPM 2.15.1, but the Compose reference uses `latest`; a future pull can change the application version.
- The NetBird proxy host is saved and Online, and the complete 1,296-character advanced snippet is active.
- The Let's Encrypt wildcard/apex certificate is assigned to the NetBird host, expires `2026-10-08 23:49:46 UTC`, and has Force SSL and HTTP/2 enabled.
- The HTTPS client path, authenticated dashboard, first-peer VPN traffic, post-restart service health, non-interactive ACME renewal path, and bounded logging are verified.
- Keep HTTP/2 enabled on the NetBird proxy host because its advanced configuration includes native gRPC routes.
- The Cloudflare DNS Write credential is stored in 1Password as `REDACTED_1PASSWORD_ITEM_TITLE_002`; never copy its value into this reference tree.

Review the [deployment record](../Documentation/Deployment.md) and [operations runbook](../Documentation/Runbook.md) before changing the live project.
