# CLI Proxy API

**Created:** 2026-08-10  
**Last updated:** 2026-09-03

I run CLI Proxy API as a Docker Compose service on `docker-main`. It moved there from `ubuntu-dev` on 2026-08-19 after its earlier move from `debian-dev` on 2026-08-13. It is available to internal clients at `https://aiproxy.alphasecunited.com`; UniFi resolves that name to Nginx Proxy Manager, and NPM forwards the request to the service's main HTTP listener.

## Current State

| Item | Current value |
|---|---|
| Deployment status | Container running; internal HTTP redirect, HTTPS route, certificate, management page, and authenticated API path verified |
| Compute | Galaxy LXC 110 `docker-main`; `192.168.40.35` on Personal-A |
| Live Compose path | `/opt/docker/cli-proxy-api` |
| Container | `cli-proxy-api` |
| Image | `eceasy/cli-proxy-api:latest`; runtime version `7.2.149` on 2026-09-03 |
| Restart policy | `unless-stopped` |
| Main listener | HTTP on TCP 8317 |
| Internal URL | `https://aiproxy.alphasecunited.com` |
| Management page | `https://aiproxy.alphasecunited.com/management.html` |
| Direct fallback | `http://192.168.40.35:8317` |
| Provider state | Six credential-state files under `auths/`; the service reports five loaded auth files and five clients at startup |

## Request Path

Internal DNS maps `aiproxy.alphasecunited.com` to NPM at `192.168.85.2`. NPM proxy host ID 26 terminates the wildcard certificate and forwards plain HTTP to `192.168.40.35:8317`. UniFi policy `Allow NPM to docker-main CLI Proxy API` admits that TCP path and logs matches.

The name has no public A record and I added no WAN ingress. HTTP redirects to HTTPS, the HTTPS endpoint returns `200`, and the presented wildcard certificate expires `2026-10-08 23:49:46 UTC`.

## Runtime Files

The live project bind-mounts these paths:

- `config.yaml` supplies the server configuration and contains secret-bearing fields, so I keep it out of this repository and at mode `0600`.
- `management.html` supplies the deployed management interface and is mounted read-only over the image copy.
- `auths/` holds live credential state. The directory contains six files, while startup reports five loaded provider auth files and five clients. The files stay out of this repository and I do not publish their contents.
- `logs/` holds application logs.
- `plugins/` holds optional plugins.

Compose publishes TCP 8317 plus callback listeners 1455, 8085, 11451, 51121, and 54545. NPM forwards only TCP 8317. The API rejects an unauthenticated `/v1/models` request with `401`; the management page is enabled and its privileged operations require the configured management key.

## Records

- [Configuration reference](Configuration/README.md)
- [Operations runbook](Documentation/Runbook.md)
- [Platform backlog](Documentation/TODO.md)
- [Internal HTTPS change record](Documentation/Change%20Records/Internal%20HTTPS%20-%202026-08-10.md)
- [Relocation to docker-main](Documentation/Change%20Records/Relocation%20to%20docker-main%20-%202026-08-19.md)
- [NPM proxy-host inventory](../Nginx%20Proxy%20Manager/Configuration/internal-proxy-hosts.md)
- [UniFi local DNS inventory](../../Infrastructure/Network/UniFi/Configuration/local-dns.md)
- [UniFi firewall inventory](../../Infrastructure/Network/UniFi/Configuration/firewall.md)
