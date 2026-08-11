# CLI Proxy API Internal HTTPS

**Created:** 2026-08-10  
**Last updated:** 2026-08-10

**Date:** 2026-08-10  
**Status:** Complete with provider onboarding remaining

## Scope

I verified the CLI Proxy API deployment on `debian-dev` and published it internally as `https://aiproxy.alphasecunited.com` through UniFi DNS and Nginx Proxy Manager.

I did not add public DNS, WAN ingress, a new API key, a management key, or a provider login. I retained no separate terminal transcript; the observed verification results are recorded below without secret values.

## Starting State

The `cli-proxy-api` container was already running from `/home/ai-agent/docker/cli-proxy-api/docker-compose.yaml` with restart policy `unless-stopped`. The root and management pages returned `200` locally on TCP 8317, while an unauthenticated `/v1/models` request returned `401`.

NPM had no `aiproxy` host, UniFi had no matching local A record, and NPM timed out when it tried to reach `192.168.40.135:8317`. The service had one configured API key but no provider authentication files, so an authenticated model request returned `200` with zero models.

## UniFi Path

I previewed and created local DNS record `6a7a605fdee8c70a32dec053`. It maps `aiproxy.alphasecunited.com` to `192.168.85.2`, uses TTL 300, and is enabled.

I previewed and created firewall policy `6a7a6060dee8c70a32dec069`, named `Allow NPM to debian-dev CLI Proxy API`. It allows TCP from `192.168.85.2` in Access-A to `192.168.40.135:8317` in Personal-A, logs matches, and permits the response path. Controller readback matched the intended source, destination, port, protocol, action, and enabled state.

## NPM Host

I created NPM proxy host ID 26 with these settings:

- domain `aiproxy.alphasecunited.com`;
- HTTP upstream `192.168.40.135:8317`;
- wildcard certificate ID 1;
- Force SSL, HTTP/2, Block Common Exploits, and WebSocket support enabled;
- HSTS, caching, and NPM access-list authentication disabled;
- request buffering, response buffering, and proxy caching disabled;
- proxy read, proxy send, and response-send timeouts set to 3,600 seconds.

NPM generated `data/nginx/proxy_host/26.conf`, and `nginx -t` passed.

## Verification

- `debian-dev` resolved `aiproxy.alphasecunited.com` to `192.168.85.2` through UniFi.
- HTTP through NPM returned `301`; HTTPS returned `200`.
- `management.html` returned `200` through the domain.
- The presented certificate had common name `*.alphasecunited.com` and expires `2026-10-08 23:49:46 UTC`.
- An unauthenticated model request returned `401`.
- An authenticated model request returned `200` with zero models, which confirms the API route but also confirms that provider onboarding is still required.
- NPM's generated configuration passed `nginx -t`.
- The DNS and firewall controller readbacks matched the intended records.
- A public resolver returned no A record for the name.

## Rollback

Route rollback means deleting NPM proxy host ID 26, UniFi DNS record `6a7a605fdee8c70a32dec053`, and UniFi firewall policy `6a7a6060dee8c70a32dec069`. The container and direct listener remain available at `http://192.168.40.135:8317`.

## Remaining Work

Complete one provider login and confirm that authenticated `/v1/models` returns the expected non-empty model list. This is application onboarding, not a DNS, firewall, or NPM fault.
