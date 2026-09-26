# Coolify

**Created:** 2026-07-24  
**Last updated:** 2026-09-25

I run Coolify on app-01 as my self-hosted deployment platform. It builds and runs applications in Docker and fronts them with its own Traefik proxy, which does the per-application Host routing for everything I publish under `*.alphsec.com`. Coolify is where a new external service gets its domain: I set the domain on the resource and the rest of the ingress chain already carries it.

## Current state

| Item | Value |
|---|---|
| Host | app-01, `192.168.80.10`, VLAN 80, Debian 13 |
| Coolify version | 4.3.23, updated 2026-09-18; read again on 2026-09-25 from `/var/www/html/config/constants.php` |
| Traefik runtime | 3.7.12 through the `traefik:v3.7` image tag, verified 2026-09-18 and 2026-09-24 |
| Public dashboard | `coolify-a1.alphsec.com`, behind Cloudflare Access |
| Local dashboard | `http://192.168.80.10:8000` |
| Docker network | `coolify`, bridge |
| Host SSH account | `coolify`, uid 9999, key-only with `NOPASSWD` sudo, since 2026-09-07; root cannot log in over SSH |

### Containers (verified 2026-09-18, listed again 2026-09-25)

| Container | Image | Role |
|---|---|---|
| coolify | `docker.io/coollabsio/coolify:4.3.23` | Control panel and API; host `8000` maps to container `8080` |
| coolify-proxy | `traefik:v3.7` | Edge proxy for deployed apps; ports 80, 443, 8080 |
| coolify-db | `postgres:15-alpine` | Coolify database |
| coolify-redis | `redis:7-alpine` | Queue and cache |
| coolify-realtime | `docker.io/coollabsio/coolify-realtime:1.0.19` | Realtime dashboard; ports 6001-6002 |
| coolify-sentinel | `docker.io/coollabsio/sentinel:1.0.1` | Host and container metrics |
| cadvisor | cAdvisor, image label 0.60.5 | Container metrics for Prometheus |

I verified the six Coolify containers healthy on 2026-09-18. On 2026-09-25 the same seven containers were running and `coolify` reported healthy. The `coolify` image carries the label `v4.5.1-33486634677`, which is not the application version. app-01 runs no Hawser agent, so Dockhand does not manage it. The local `/login` and `/api/health` endpoints both returned HTTP 200 after the update and again at 12:13 PM Eastern. The [4.3.23 update record](Documentation/Change%20Records/Update%20to%204.3.23%20-%202026-09-18.md) holds the command, checks, and retained follow-up evidence.

## Installation

I installed Coolify with its official automated installer. My shell history on app-01 contains `curl -fsSL https://cdn.coollabs.io/coolify/install.sh | sudo bash` twice. The running core containers use `/data/coolify/source/docker-compose.yml` and `/data/coolify/source/docker-compose.prod.yml`; the proxy uses `/data/coolify/proxy/docker-compose.yml`. I confirmed the installer is the [method recommended by the Coolify team](https://coolify.io/docs/start-with-self-hosted#choose-installation-method). See [Architecture](Documentation/Architecture.md) for the Compose layout.

## Ingress

Two hostnames reach this host through the `edge-01` Cloudflare Tunnel:

- `coolify-a1.alphsec.com` goes straight to the control panel on port 8000, behind Cloudflare Access with two allowed identities and a path-scoped bypass for the GitHub webhook.
- `*.alphsec.com` arrives on port 80 at the Traefik proxy after passing through Caddy on edge-01. Traefik routes by Host to the deployed container.

A UniFi policy lets edge-01 reach this host only on TCP 80 and 8000. See the [Coolify Access Hardening record](../../Infrastructure/Network/Cloudflare/Documentation/Change%20Records/Coolify%20Access%20Hardening%20-%202026-07-22.md).

## Records

- [Architecture](Documentation/Architecture.md)
- [Update to 4.3.23](Documentation/Change%20Records/Update%20to%204.3.23%20-%202026-09-18.md)
- [Non-root server account and root SSH disabled](Documentation/Change%20Records/Non-Root%20Server%20Account%20and%20Root%20SSH%20Disabled%20-%202026-09-07.md)
- [Traefik 3.7 minor update](Documentation/Change%20Records/Traefik%203.7%20Minor%20Update%20-%202026-08-09.md)
- [Traefik 3.6 patch update](Documentation/Change%20Records/Traefik%203.6%20Patch%20Update%20-%202026-08-02.md)
- [External Service Ingress design](../../Architecture/External-Service-Ingress.md)
- [Cloudflare Tunnel edge-01](../../Infrastructure/Network/Cloudflare/Configuration/edge-01.md)
- [Caddy edge proxy](../Caddy/README.md)
- [Cloudflare Access applications](../../Infrastructure/Network/Cloudflare/Configuration/applications.md)

## Layout

- `Documentation/`: architecture and records for this platform.
- `Evidence/`: retained command evidence for dated Coolify changes.
