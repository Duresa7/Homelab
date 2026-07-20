# Nginx Proxy Manager Configuration

**Created:** 2026-07-11  
**Last updated:** 2026-07-20

The live Compose project is `/opt/docker/nginx-proxy-manager` on `docker-network`. This folder holds reader-editable reference configuration.

## Files

- `docker-compose.yml` defines the NPM service, persistent bind mounts, published ports, bounded `json-file` logging (`10m` × `3`), health check, restart policy, and fixed address `172.31.85.10` on external Docker network `proxy`.
- `netbird-advanced-config.conf` is the applied NPM Advanced snippet for `<YOUR_NETBIRD_DOMAIN>`. It routes the NetBird API/OAuth2, WebSocket, signal, management, and gRPC paths to `netbird-server:80` while the default proxy host points to `netbird-dashboard:80`.

## Runtime State

NPM writes its database, proxy-host state, & generated Nginx files under `data/`. ACME account state & certificates live under `letsencrypt/`. Both paths are runtime bind mounts rather than reader-editable configuration.

## Operational Notes

- The external `proxy` network uses subnet `172.31.85.0/24` and must exist before Compose starts.
- NetBird's live `reverseProxy.trustedHTTPProxies` entry must match NPM's fixed address `172.31.85.10/32`.
- The verified runtime is NPM 2.15.1, but the Compose reference uses `latest`; a future pull can change the application version.
- The NetBird proxy host is saved and Online, and the complete 1,296-character advanced snippet is active.
- The Let's Encrypt wildcard/apex certificate is assigned to the NetBird host, expires `2026-10-08 23:49:46 UTC`, and has Force SSL and HTTP/2 enabled.
- The HTTPS client path, authenticated dashboard, first-peer VPN traffic, post-restart service health, non-interactive ACME renewal path, and bounded logging are all verified.
- Keep HTTP/2 enabled on the NetBird proxy host because its advanced configuration includes native gRPC routes.
- Supply `<YOUR_CLOUDFLARE_DNS_TOKEN>` through the NPM certificate form when creating the DNS-01 certificate.

Review the [deployment record](../Documentation/Deployment.md) and [operations runbook](../Documentation/Runbook.md) before changing the live project.
