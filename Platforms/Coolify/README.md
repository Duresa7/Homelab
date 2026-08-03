# Coolify

**Created:** 2026-07-24  
**Last updated:** 2026-08-02

I run Coolify on app-01 as my self-hosted deployment platform. It builds & runs applications in Docker & fronts them with its own Traefik proxy, which does the per-application Host routing for everything I publish under `*.alphsec.com`. Coolify is where a new external service gets its domain: I set the domain on the resource & the rest of the ingress chain already carries it.

## Current state

| Item | Value |
|---|---|
| Host | app-01, `192.168.80.10`, VLAN 80, Debian 13 |
| Coolify version | 4.1.2 |
| Traefik runtime | 3.6.25 through the `traefik:v3.6` image tag |
| Public dashboard | `coolify-a1.alphsec.com`, behind Cloudflare Access |
| Local dashboard | `http://192.168.80.10:8000` |
| Docker network | `coolify`, bridge |

### Containers (verified 2026-08-02)

| Container | Image | Role |
|---|---|---|
| coolify | `ghcr.io/coollabsio/coolify:4.1.2` | Control panel & API; host `8000` maps to container `8080` |
| coolify-proxy | `traefik:v3.6` | Edge proxy for deployed apps; ports 80, 443, 8080 |
| coolify-db | `postgres:15-alpine` | Coolify database |
| coolify-redis | `redis:7-alpine` | Queue & cache |
| coolify-realtime | `ghcr.io/coollabsio/coolify-realtime:1.0.16` | Realtime dashboard; ports 6001-6002 |
| coolify-sentinel | `ghcr.io/coollabsio/sentinel:0.0.21` | Host & container metrics |

All six reported healthy on 2026-08-02.

## Ingress

Two hostnames reach this host through the `edge-01` Cloudflare Tunnel:

- `coolify-a1.alphsec.com` goes straight to the control panel on port 8000, behind Cloudflare Access with two approved identities & a path-scoped bypass for the GitHub webhook.
- `*.alphsec.com` arrives on port 80 at the Traefik proxy after passing through Caddy on edge-01. Traefik routes by Host to the deployed container.

A UniFi policy lets edge-01 reach this host only on TCP 80 & 8000. See the [Coolify Access Hardening record](../../Infrastructure/Network/Cloudflare/Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md).

## Records

- [Architecture](Documentation/Architecture.md)
- [Traefik 3.6 patch update](Documentation/Change%20Records/Coolify%20Traefik%203.6%20Patch%20Update%20-%202026-08-02.md)
- [External Service Ingress design](../../Architecture/External-Service-Ingress.md)
- [Cloudflare Tunnel edge-01](../../Infrastructure/Network/Cloudflare/Configuration/edge-01.md)
- [Caddy edge proxy](../Caddy/README.md)
- [Cloudflare Access applications](../../Infrastructure/Network/Cloudflare/Configuration/applications.md)

## Layout

- `Documentation/`: architecture & records for this platform.
- `Evidence/`: retained command evidence for dated Coolify changes.
