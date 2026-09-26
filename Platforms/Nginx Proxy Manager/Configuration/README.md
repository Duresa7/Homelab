# Nginx Proxy Manager Configuration

**Created:** 2026-07-11  
**Last updated:** 2026-09-25

The live Compose project is `/opt/docker/nginx-proxy-manager` on `docker-network`. This folder holds reader-editable reference configuration.

## Files

- `docker-compose.yml` defines the NPM service (image pinned to `jc21/nginx-proxy-manager:2.15.1`, label `dockhand.update: "false"`), persistent bind mounts, published ports, bounded `json-file` logging (`10m`, 3 files), health check, restart policy, and fixed address `172.31.85.10` on external Docker network `proxy`.
- `netbird-advanced-config.conf` is the applied NPM Advanced snippet for `netbird.alphasecunited.com`. It routes the NetBird API/OAuth2, WebSocket, signal, management, and gRPC paths to `netbird-server:80` while the default proxy host points to `netbird-dashboard:80`.
- `internal-proxy-hosts.md` is the current inventory of the live proxy hosts, upstream schemes, addresses, ports, and compatibility notes. It is the one place that states the host count.

## Runtime State

NPM writes its database, proxy-host state, and generated Nginx files under `data/`. ACME account state and certificates live under `letsencrypt/`. Both paths are runtime bind mounts rather than reader-editable configuration.

## Operational Notes

- The external `proxy` network uses subnet `172.31.85.0/24` and must exist before Compose starts.
- NetBird's live `reverseProxy.trustedHTTPProxies` entry must match NPM's fixed address `172.31.85.10/32`.
- The runtime is NPM 2.15.1. Since 2026-09-25 the Compose reference pins that tag, so a pull cannot change the version.
- The NetBird proxy host is saved and Online, and the complete 1,296-character advanced snippet is active.
- The Let's Encrypt wildcard and apex certificate (ID 1) is assigned to every live host with Force SSL and HTTP/2. It renews automatically; on 2026-09-24 it expired 2026-12-08 at 3:03 AM UTC.
- The HTTPS client path, authenticated dashboard, first-peer VPN traffic, post-restart service health, non-interactive ACME renewal path, and bounded logging are all verified.
- Keep HTTP/2 enabled on the NetBird proxy host because its advanced configuration includes native gRPC routes.
- The internal application hosts use certificate ID 1, Force SSL, HTTP/2, Block Common Exploits, and WebSocket support. Immich also disables request buffering and uses a 50,000 MiB body limit with 600-second timeouts. CLI Proxy API disables buffering and caching and uses 3,600-second timeouts.
- UniFi owns the matching local A records and the narrow policies from NPM to the backend web listeners. Public DNS has no matching A records.

Review the [deployment record](../Documentation/Deployment.md) and [operations runbook](../Documentation/Runbook.md) before changing the live project.
