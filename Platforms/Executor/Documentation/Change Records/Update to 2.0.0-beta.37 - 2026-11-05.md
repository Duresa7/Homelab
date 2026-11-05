# Update to 2.0.0-beta.37

**Created:** 2026-11-05  
**Last updated:** 2026-11-05

On 2026-11-05 I moved Executor 2 on `docker-blue` from 2.0.0-beta.34 to 2.0.0-beta.37, the build tagged the morning Executor v2 was announced publicly. v2 has no stable release yet, and every v2 build is still a GitHub pre-release.

## What changed upstream

The public repository, `UsefulSoftwareCo/executor`, publishes each v2 release as one squashed "Export" commit on its tag, and `apps/cli/CHANGELOG.md` says only "Nightly beta" for every version. What changed is in the `.changeset/` notes and the files between the `executor@2.0.0-beta.34` and `executor@2.0.0-beta.37` tags (165 files):

- The bundled Motel collector no longer evicts on every export once its 1 GiB store is full. It now evicts to 90% and stores without evicting until it fills again. Upstream measured an idle collector falling from about 9% of a core to under 1%. My `motel-data` held 1.4 GB before the update.
- OAuth authorization-code grants keep their original redirect URI and reuse it when refreshing.
- Dynamic client registrations without `application_type` are treated as native when a callback is loopback or private-use, so a client that registers a web callback beside one is no longer refused.
- Provider `hosts` may contain underscores (host protocol 14). Apps on earlier framework releases keep running.
- A failed storage upgrade reports its storage version, SQLSTATE and error classes at startup.
- `/_executor/watch.js` is gone. App pages inline their version watcher.
- `better-auth` went from 1.7.5 to 1.7.16. The apps framework went from `0.0.1-beta.117` to `0.0.1-beta.120`.

Before the update I compared the two source trees. The storage schema list in `packages/sdk/src/implementation/storage-migrations.ts` is identical and the tree holds the same three SQL files, so Executor's own data takes no migration. Every environment variable in my Compose file (`BETTER_AUTH_URL`, `EXECUTOR_APPS_ALLOW_PRIVATE_FETCH`, `EXECUTOR_URL_ALLOW_HTTP_ORIGINS`, `EXECUTOR_CATALOG_URL`, `EXECUTOR_APP_UI_BASE_URL`, `EXECUTOR_DISABLE_ANALYTICS`, `DO_NOT_TRACK`, `EXECUTOR_APP_WORKERS`) is read the same way in both trees.

## Changes

1. I confirmed the live `/opt/docker/executor-v2/docker-compose.yml` matched the [Compose reference](../../Configuration/docker-compose.yml) by SHA-256 before touching it.
2. I pulled `ghcr.io/usefulsoftwareco/executor-selfhost:2.0.0-beta.37@sha256:23b1f96c4098b48ec8bdf71da76bcd6c656ea7c2d390d96287d82442c39d7230` while beta.34 kept serving. The index digest came from GHCR's manifest endpoint, the same lookup that returns beta.34's pinned digest.
3. Because every SSH call runs through Executor, I ran the switch as a detached root script. It stopped the container at 3:45:18 PM (stopped at 3:45:34 PM), copied `data` (178 MB) to `data.pre-beta37` as a rollback point, swapped the image pin in the Compose file, and ran `docker compose up -d executor`. The container started at 3:45:35 PM and reported healthy with zero restarts.
4. I updated the [Compose reference](../../Configuration/docker-compose.yml). Its SHA-256 matches the live file.
5. After verification I deleted `data.pre-beta37`, the script and its log from `docker-blue`.

I did not redeploy the four bearer apps. They still run on framework `0.0.1-beta.117`, which beta.37 keeps serving, and [bearer-apps.config.mjs](../../Scripts/bearer-apps.config.mjs) still names that version.

## Verification

- `docker inspect` reports the beta.37 digest, `healthy`, zero restarts. `docker stats` showed 0.62% CPU and 812 MiB of the 1.5 GiB limit a few minutes after start. The log tail showed only workerd's `nodejs_compat` notices and routine info lines.
- `framework.release` returns `0.0.1-beta.120`.
- One call per bearer app succeeded: `ssh` ran commands on `docker_blue`, `unifi` listed networks (24 in total), `wazuh` listed 15 active agents, and `cloudflare` ran an OpenAPI search. The Cloudflare `mcp.search` call paused for Executor's approval prompt and ran once I approved it. That `cloudflare` app is an OAuth install, not the bearer app the README's table describes, so the prompt belongs to that install rather than to this update.
- An OAuth-signed-in MCP client kept working across the restart without signing in again. The personal access token `Executor API Token - ubuntu-dev agents` ran an SSH call through `/mcp`.
- `/.well-known/oauth-authorization-server` returns an issuer, a registration endpoint and `S256`. An unauthenticated POST to `/mcp` answers 401.
- `https://executor.alphasecunited.com/login` answers 200 with the [URL.parse polyfill](Safari%2017%20URL.parse%20Polyfill%20-%202026-11-02.md) as the first element in `<head>`, for both plain and gzip-accepting requests.

## Rollback

The storage schema did not change, so pinning `2.0.0-beta.34@sha256:1af389b0a9ffca783c175a514df1667d3e911bd01df63262c9908d90872900e3` again and recreating the container should return to the old build. The beta.34 image is still on `docker-blue`.
