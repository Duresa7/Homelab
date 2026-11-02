# App Page Domain

**Created:** 2026-11-02  
**Last updated:** 2026-11-02

On 2026-11-02 I gave Executor 2 an app domain, so an app that ships a page can be opened in a browser. Before this, `appUi.location` answered `status: "unavailable"` with `reason: "no_app_domain"` for every app, because self-host has no default.

## How Executor builds a page address

`EXECUTOR_APP_UI_BASE_URL` names a base origin. Executor 2.0.0-beta.34 puts each app at `<app-slug>.<org-slug>.<base hostname>` with the base's scheme and port, and routes a request on any host below the base to the app it names. The organization slug is `executor`, so with the base `https://apps.alphasecunited.com` an app's page is `https://<app-slug>.executor.apps.alphasecunited.com`. That name is two labels below `alphasecunited.com`, so NPM's certificate 1 (`*.alphasecunited.com`) does not cover it.

## Changes

1. **NPM certificate 2.** I requested a Let's Encrypt DNS-01 certificate for `*.executor.apps.alphasecunited.com` through NPM's API, with the same Cloudflare DNS-01 provider, key type and propagation time as certificate 1 and the zone-scoped DNS Write token NPM already uses. It was issued at 6:18 AM and expires 2027-01-31.
2. **NPM proxy host 38.** `*.executor.apps.alphasecunited.com` forwards over HTTP to `192.168.40.39:4400`, the same listener as host 37. I copied host 37's settings: certificate 2 (host 37 uses certificate 1), Force SSL, HTTP/2, Block Common Exploits, WebSocket support, HSTS off, and the same advanced configuration (no proxy buffering or caching, 3,600-second proxy read, proxy send and response-send timeouts). Readback reported `nginx_online: true` with no error. The UniFi policy `Allow NPM to docker-blue Executor` already allowed the path.
3. **UniFi local DNS.** UniFi local DNS has no wildcard record, so each app page gets its own A record to `192.168.85.2`. The first is `book-digest.executor.apps.alphasecunited.com`, record `6ae87f44e2482aecb9604963`.
4. **Executor.** I copied the live Compose file to [Backups](../../../../Backups/docker-blue-executor-v2-docker-compose-2026-11-02.yml), added `EXECUTOR_APP_UI_BASE_URL: https://apps.alphasecunited.com`, checked the file with `docker compose config --quiet`, and recreated the container with `docker compose up -d executor` from a detached shell, because the SSH call itself runs through Executor. The container started at 7:17 AM and reported healthy. I then deleted the host copy. The [Compose reference](../../Configuration/docker-compose.yml) matches the live file.

## Verification

- `https://executor.alphasecunited.com/` answered 307 after the recreate, and Executor MCP calls worked again.
- `book-digest.executor.apps.alphasecunited.com` resolves to `192.168.85.2`, and NPM presents `CN=*.executor.apps.alphasecunited.com`, valid to 2027-01-31.
- `appUi.location` returns `status: "ready"` with `https://book-digest.executor.apps.alphasecunited.com`.
- A browser-style navigation to that page answers 302 to `https://executor.alphasecunited.com/app-auth?request=...`, Executor's sign-in handoff. A plain request without browser headers gets 403 `App unavailable.` from Executor, which is the expected answer for a request that cannot sign in.

## Adding another app page

Deploy the app, read its address from `appUi.location`, and add a UniFi A record for that host to `192.168.85.2`. NPM host 38 and certificate 2 already cover it. Renaming an app changes its slug, and with it the host name and the DNS record it needs.
