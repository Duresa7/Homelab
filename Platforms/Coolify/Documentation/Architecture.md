# Coolify Architecture

**Created:** 2026-07-24  
**Last updated:** 2026-08-09

Coolify runs as a six-container stack on app-01 & manages a Traefik proxy that routes public traffic to the applications I deploy. This document covers how the pieces fit & how a deployment turns into a working URL. The live state table is in the [platform README](../README.md); the end-to-end ingress path is in the [External Service Ingress design](../../../Architecture/External-Service-Ingress.md).

## The stack

Coolify installs itself with Docker Compose & keeps everything on the `coolify` bridge network. The `coolify` container is the control panel & API; it publishes port 8000 on the host for the dashboard. `coolify-db` (PostgreSQL 15) holds state, `coolify-redis` runs the queue, `coolify-realtime` serves the live dashboard over ports 6001-6002, & `coolify-sentinel` collects host & container metrics. Only ports 80, 443, & 8000 matter to ingress, & the edge firewall permits just 80 & 8000 from edge-01.

## Traefik & per-app routing

`coolify-proxy` is Traefik v3.7, listening on host ports 80, 443, & 8080. When I deploy an application & give it a domain, Coolify writes Traefik router labels on that container so Traefik forwards requests with a matching Host header to it. Traefik holds the routing table for every deployed app. Caddy on edge-01 doesn't know the individual hostnames; it hands the whole wildcard to Traefik on port 80.

## How a deployment becomes a URL

Publishing `<name>.alphsec.com` takes one input from me: the domain field on the Coolify resource. The wildcard DNS record, the wildcard tunnel ingress rule, & the wildcard Caddy site already exist, so I add no DNS, tunnel, or Caddy configuration. Coolify writes the Traefik router, Traefik starts matching the Host, & the service answers. TLS is Cloudflare's at the edge, so the app speaks plain HTTP inside the chain.

## Control-panel path vs app path

The dashboard & the apps take different routes on purpose. `coolify-a1.alphsec.com` bypasses Caddy & Traefik & hits the control panel on port 8000, so the panel stays reachable even while the proxy is being reconfigured. Deployed apps ride `*.alphsec.com` through Caddy & Traefik.

## Security notes

- Only `coolify-a1.alphsec.com` sits behind Cloudflare Access. Any other `*.alphsec.com` host is public once deployed, so I add Access or app-level auth for anything that shouldn't be open.
- The GitHub webhook uses a path-scoped Access bypass on `coolify-a1.alphsec.com/webhooks/source/github/events`; child paths & the rest of the host require an approved identity. See the [Access applications](../../../Infrastructure/Network/Cloudflare/Configuration/applications.md).
- The UniFi edge policy limits edge-01 to TCP 80 & 8000 on this host.
