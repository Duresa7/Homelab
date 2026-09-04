# Executor Initial Deployment

**Created:** 2026-08-30  
**Last updated:** 2026-08-31

**Date:** 2026-08-30  
**Status:** Deployed and healthy; initial administrator claim remains

## Outcome

I deployed Executor 1.6.7 on `docker-blue` and published it internally as `https://mcp.alphasecunited.com`. The container, reverse proxy, internal DNS, TLS, and least-privilege cross-zone firewall path are operational. No public DNS record or inbound WAN rule was added.

## Source Selection

The official GitHub container package listed 1.6.7 as the newest stable release when I deployed it. I pinned both that tag and the multi-architecture digest `sha256:c8dd83a5dba8ac992dfe1ded4aa65ae4e7f52ec31fddbe2af5b49ffebe5bbfa7` rather than following a mutable tag.

## Implementation

1. Created `/opt/docker/executor` and a root-owned `data` directory on `docker-blue`.
2. Installed the versioned Compose definition and started the pinned image.
3. Disabled local-network tools, local STDIO MCP servers, and analytics.
4. Added Nginx Proxy Manager proxy host ID 27 for `mcp.alphasecunited.com` to `192.168.40.39:4788`, using certificate ID 1, Force SSL, HTTP/2, WebSockets, exploit blocking, and 3,600-second streaming timeouts.
5. Added UniFi local DNS record `6a94416df9e5db24858d3005`: `mcp.alphasecunited.com` to `192.168.85.2`, TTL 300.
6. Added UniFi policy `6a94416df9e5db24858d3008`, `Allow NPM to docker-blue Executor`, at index 10005. It permits TCP only from `192.168.85.2` in AlphaSec-Access to `192.168.40.39:4788` in Internal and logs matches.

I kept direct IP and port selectors in the new policy. The rule has one source, one destination, and one service port, so a new reusable network or port object would add indirection without reducing maintenance. It also avoids having a later object expansion silently broaden this application path.

## Verification

- Docker reported the container running and healthy with zero crash restarts.
- The direct `/api/health` endpoint returned `{"status":"ok"}`.
- Internal DNS returned `192.168.85.2`; Cloudflare DNS-over-HTTPS returned NXDOMAIN for the name.
- Plain HTTP redirected to `https://mcp.alphasecunited.com/` with `301`.
- HTTPS `/` returned `200`; HTTPS `/api/health` returned healthy.
- The presented Let's Encrypt certificate covered `*.alphasecunited.com` and expires 2026-10-08.
- An unauthenticated request to `/mcp` returned `401`, confirming that it reached Executor and authentication was enforced.
- Nginx configuration validation passed and Nginx Proxy Manager remained healthy.
- After a controlled Executor restart, both generated key files were unchanged and the container and HTTPS health endpoint recovered.
- One post-restart sample showed 0.23 percent CPU, 114.7 MiB memory, and seven processes. This is a point-in-time idle measurement, not a capacity limit.

## Remaining Administrator Step

The first-run setup form is reachable at `https://mcp.alphasecunited.com`. I left administrator creation as a manual step so a unique credential can be chosen and stored outside this repository. Until that account is claimed, the instance should be treated as awaiting application bootstrap even though the deployment and network path are healthy.
