# Deployment

**Created:** 2026-09-27  
**Last updated:** 2026-09-27

**Status:** Complete  
**Date:** 2026-09-27

I deployed Homarr 1.77.2 on CT 110 `docker-main` and published it internally at `https://dashboard.alphasecunited.com` through Nginx Proxy Manager. This replaces the address of the application I [retired on 2026-09-26](../../../../Archive/Platforms/Homelab%20Dashboard/Documentation/Change%20Records/Retirement%20-%202026-09-26.md). I kept its source archive intact.

## Official deployment method

Before deployment I checked the [official Docker instructions](https://homarr.dev/docs/getting-started/installation/docker/), [environment variables](https://homarr.dev/docs/advanced/environment-variables/) and [onboarding instructions](https://homarr.dev/docs/getting-started/after-the-installation/). I selected the [current 1.77.2 release](https://github.com/homarr-labs/homarr/releases/tag/v1.77.2), with source commit `18dafb1276d8ff66d1be1b149c74f80dbf94f78d`.

I used the official single-container Compose layout, persistent `/appdata`, port 7575, `unless-stopped`, and a 64-character hexadecimal encryption key. My local choices were a pinned release tag, a host-IP-specific port binding, bounded logs, and loading the key from a mode-0600 `.env` file. I omitted the optional Docker socket because no Docker integration was requested.

## Deployment and access

| Step | Action and observed result |
|---|---|
| Preflight, 8:22 AM Eastern | `docker-main` had approximately 13 GiB available RAM and 39 GiB free root storage, Compose 5.5.1, 14 running containers, no listener on 7575 and no `/opt/docker/homarr`. NPM had 23 live hosts and no dashboard host. UniFi had 29 DNS records and no dashboard record. |
| Container | I created `/opt/docker/homarr/docker-compose.yml`, generated the key directly into `.env`, validated Compose without printing expanded configuration, pulled the image and started `homarr`. The mounted data path is `/opt/docker/homarr/appdata`. `/api/health/ready` returned 200. |
| Firewall | Through UniFi MCP I added only TCP 7575 to policy `6a60fd2c2d027bb05525a873`, `Allow NPM to docker-main web UIs`. Its destination ports are now `2283,3000,3002,3003,3004,6060,7575`. Source remains the reverse-proxy object resolving to `192.168.85.2`; destination remains `192.168.40.35`. |
| NPM | I authenticated through the existing API and created proxy host 34 for `dashboard.alphasecunited.com`, forwarding HTTP to `192.168.40.35:7575`. It uses shared certificate 1, Force SSL, HTTP/2, WebSockets and Block Common Exploits, with HSTS and caching off. Readback reported `nginx_online=true`, no nginx error, and 24 live hosts. |
| Administrator | I used Homarr's own onboarding endpoints after checking their definitions in the selected release. I created the admin from the standard application account, disabled analytics and crawler indexing, and completed onboarding without integrations. A fresh authenticated session passed first directly and then through HTTPS. No credentials or session tokens were retained in evidence. |
| DNS | Through UniFi MCP I created enabled A record `6ab90b1425574794b9328224`, `dashboard.alphasecunited.com` to `192.168.85.2`, TTL 300. Readback returned 30 records, 24 pointing to NPM. Public DNS returned NXDOMAIN. |

The pulled image digest is `sha256:f0fb462299af9749a72f11040fd3f604d1c4976b3d9a137ae5021b7f44d980f5`. The first resource sample showed 255.2 MiB container memory use. I did not resize the LXC or change other applications.

## Verification

At 8:25 AM Eastern, HTTP redirected to HTTPS with 301, TLS validation passed, the HTTPS root and readiness endpoint returned 200, and a fresh login reached `/manage` with 200. NPM's `nginx -t` passed, its container stayed healthy, and a request from `docker-network` to Homarr's backend returned 200.

I checked all 24 HTTPS hosts with certificate validation enabled. Every host returned its expected response or redirect; App Portal retained its existing root-path 404. None returned a gateway error. I then restarted only `homarr`. At 8:26 AM Eastern, readiness returned 200, onboarding remained at `finish`, and another fresh HTTPS login succeeded, verifying persistence. The browser on Jedi PC loaded Homarr's login form at the requested hostname.

The [evidence exports](../../Evidence/Deployment%20-%202026-09-27/Exports/) retain the Compose command and result, runtime and nginx checks, restart result, filtered proxy definition, DNS/firewall readback, HTTPS host checks and post-restart authentication result. They are structured exports, not complete timestamped terminal transcripts. No separate raw transcript is retained for preflight, onboarding, DNS/firewall writes, NPM authentication/creation, public DNS lookup or browser inspection; their observed results are recorded above.

I rechecked the deployment when completing this record: Homarr was still running the pinned image with zero automatic restarts, Compose validation passed, and backend and HTTPS readiness both returned 200 with TLS verification successful. The [completion export](../../Evidence/Deployment%20-%202026-09-27/Exports/Completion-Verification.json) records the command and result. I reviewed the seven earlier exports and added explicit Git exceptions for all eight evidence files.

I created no snapshot or backup. No temporary file contains credentials; the deployment's `.env` is retained runtime configuration. The application is deployed and accessible. Board customization, service integrations, and adding it to uptime monitoring remain separate work; none was configured as part of this deployment.
