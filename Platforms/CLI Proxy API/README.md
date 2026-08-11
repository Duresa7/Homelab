# CLI Proxy API

**Created:** 2026-08-10  
**Last updated:** 2026-08-10

I run CLI Proxy API as a Docker Compose service on `debian-dev`. It is available to internal clients at `https://aiproxy.alphasecunited.com`; UniFi resolves that name to Nginx Proxy Manager, and NPM forwards the request to the service's main HTTP listener.

## Current State

| Item | Current value |
|---|---|
| Deployment status | Container running; internal HTTP redirect, HTTPS route, certificate, management page, and authenticated API path verified |
| Compute | Galaxy VM 102 `debian-dev`; guest hostname `debian-dev`; `192.168.40.135` on Personal-A |
| Live Compose path | `/home/ai-agent/docker/cli-proxy-api` |
| Container | `cli-proxy-api` |
| Image | `eceasy/cli-proxy-api:latest`; deployed digest begins `sha256:3f7a734784f4` |
| Restart policy | `unless-stopped` |
| Main listener | HTTP on TCP 8317 |
| Internal URL | `https://aiproxy.alphasecunited.com` |
| Management page | `https://aiproxy.alphasecunited.com/management.html` |
| Direct fallback | `http://192.168.40.135:8317` |
| Provider state | No provider authentication files; an authenticated `/v1/models` request returns zero models |

## Request Path

Internal DNS maps `aiproxy.alphasecunited.com` to NPM at `192.168.85.2`. NPM proxy host ID 26 terminates the wildcard certificate and forwards plain HTTP to `192.168.40.135:8317`. UniFi policy `Allow NPM to debian-dev CLI Proxy API` admits that TCP path and logs matches.

The name has no public A record and I added no WAN ingress. HTTP redirects to HTTPS, the HTTPS endpoint returns `200`, and the presented wildcard certificate expires `2026-10-08 23:49:46 UTC`.

## Runtime Files

The live project bind-mounts these paths:

- `config.yaml` supplies the server configuration and contains secret-bearing fields, so I keep it out of this repository and at mode `0600`.
- `auths/` holds provider authentication files. It currently contains only its placeholder and no provider authentication file.
- `logs/` holds application logs.
- `plugins/` holds optional plugins.

Compose publishes TCP 8317 plus callback listeners 1455, 8085, 11451, 51121, and 54545. NPM forwards only TCP 8317. The API rejects an unauthenticated `/v1/models` request with `401`; the management page is enabled and its privileged operations require the configured management key.

## Records

- [Configuration reference](Configuration/README.md)
- [Operations runbook](Documentation/Runbook.md)
- [Platform backlog](Documentation/TODO.md)
- [Internal HTTPS change record](Documentation/Change%20Records/Internal%20HTTPS%20-%202026-08-10.md)
- [NPM proxy-host inventory](../Nginx%20Proxy%20Manager/Configuration/internal-proxy-hosts.md)
- [UniFi local DNS inventory](../../Infrastructure/Network/UniFi/Configuration/local-dns.md)
- [UniFi firewall inventory](../../Infrastructure/Network/UniFi/Configuration/firewall.md)
