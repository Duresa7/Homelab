# Coolify Architecture

**Created:** 2026-07-24  
**Last updated:** 2026-09-18

Coolify runs as a six-container stack on app-01 and manages a Traefik proxy that routes public traffic to the applications I deploy. This document covers how the pieces fit and how a deployment turns into a working URL. The live state table is in the [platform README](../README.md); the end-to-end ingress path is in the [External Service Ingress design](../../../Architecture/External-Service-Ingress.md).

## The stack

Coolify installs itself with Docker Compose and keeps everything on the `coolify` bridge network. The `coolify` container is the control panel and API; it publishes port 8000 on the host for the dashboard. `coolify-db` (PostgreSQL 15) holds state, `coolify-redis` runs the queue, `coolify-realtime` serves the live dashboard over ports 6001-6002, and `coolify-sentinel` collects host and container metrics. Only ports 80, 443, and 8000 matter to ingress, and the edge firewall permits just 80 and 8000 from edge-01.

I confirmed the installation method from app-01's shell history: the official `install.sh` was invoked through `curl` and `sudo bash`. The live Docker labels identify Compose project `source`, with `/data/coolify/source/docker-compose.yml` and `/data/coolify/source/docker-compose.prod.yml` supplying the control panel, PostgreSQL, Redis, and realtime containers. Traefik belongs to the separate `coolify-proxy` project at `/data/coolify/proxy/docker-compose.yml`. Sentinel has no Compose project labels. These observations establish an installer-based deployment; I did not establish whether the Compose files were edited manually later.

I updated the control panel with the official `upgrade.sh` on 2026-09-18. That restarted the four core Compose containers; Traefik, Sentinel, and cAdvisor retained their container IDs. The [update record](Change%20Records/Update%20to%204.3.23%20-%202026-09-18.md) holds the exact invocation and verification.

## Traefik and per-app routing

`coolify-proxy` is Traefik v3.7, listening on host ports 80, 443, and 8080. When I deploy an application and give it a domain, Coolify writes Traefik router labels on that container so Traefik forwards requests with a matching Host header to it. Traefik holds the routing table for every deployed app. Caddy on edge-01 doesn't know the individual hostnames; it hands the whole wildcard to Traefik on port 80.

## How a deployment becomes a URL

Publishing `<name>.alphsec.com` takes one input from me: the domain field on the Coolify resource. The wildcard DNS record, the wildcard tunnel ingress rule, and the wildcard Caddy site already exist, so I add no DNS, tunnel, or Caddy configuration. Coolify writes the Traefik router, Traefik starts matching the Host, and the service answers. TLS is Cloudflare's at the edge, so the app speaks plain HTTP inside the chain.

## Control-panel path vs app path

The dashboard and the apps take different routes on purpose. `coolify-a1.alphsec.com` bypasses Caddy and Traefik and hits the control panel on port 8000, so the panel stays reachable even while the proxy is being reconfigured. Deployed apps ride `*.alphsec.com` through Caddy and Traefik.

## Security notes

- Only `coolify-a1.alphsec.com` sits behind Cloudflare Access. Any other `*.alphsec.com` host is public once deployed, so I add Access or app-level auth for anything that shouldn't be open.
- The GitHub webhook uses a path-scoped Access bypass on `coolify-a1.alphsec.com/webhooks/source/github/events`; child paths and the rest of the host require an approved identity. See the [Access applications](../../../Infrastructure/Network/Cloudflare/Configuration/applications.md).
- The UniFi edge policy limits edge-01 to TCP 80 and 8000 on this host.
