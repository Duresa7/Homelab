# Executor Runbook

**Created:** 2026-08-30  
**Last updated:** 2026-10-31

These steps cover Executor 2 on `docker-blue` (`192.168.40.39`). The current state is on the [platform front page](../README.md). Executor 1's procedures went with it on 2026-10-31 and are in this file's history.

## Deployment Layout

| Path | Purpose |
|---|---|
| `/opt/docker/executor-v2/docker-compose.yml` | Live Compose definition |
| `/opt/docker/executor-v2/data` | PGlite database, app source and builds, `auth-secret.key`, `encryption.key`; UID 1000, mode 0700 |
| `/opt/docker/executor-v2/motel-data` | The bundled trace collector's store; UID 1000, mode 0700 |
| `Platforms/Executor/Configuration/docker-compose.yml` | Versioned Compose reference |

The two directories must belong to UID 1000 before the first start, because the container starts as that user and cannot chown them. I do not put the data directory, its keys, or any token in Git.

## Routine Checks

On `docker-blue`:

```bash
cd /opt/docker/executor-v2
docker compose ps
docker compose logs --tail 100 executor
docker stats executor-v2 --no-stream
curl -fsS http://192.168.40.39:4400/health
```

From an internal client: `curl -fsS https://executor.alphasecunited.com/health` returns `{"status":"ok"}`, and a POST to `/mcp` without a token returns `401` with a `WWW-Authenticate: Bearer resource_metadata=...` header.

Through the MCP endpoint, `search({ query: "<app>" })` should list each app's tools: 15 for `ssh`, 5 for `unifi`, 41 for `wazuh`, 4 for `cloudflare`, as counted on 2026-10-31. Tool counts change when a server changes its surface, so record a new count rather than treating these as invariants. One read per app proves its account: `list-connections` on `ssh`, `unifi_execute` with `unifi_list_networks` on `unifi`, `validate_wazuh_connection` on `wazuh`, `whoami` on `cloudflare`.

## Updating

1. Read every beta's release notes from the running version forward. The beta publishes about daily.
2. Resolve the new tag's digest from `ghcr.io/usefulsoftwareco/executor-selfhost` and change the tag and digest in the Compose reference together.
3. Install the file on `docker-blue`, then `docker compose pull && docker compose up -d`. Startup runs the database's data steps before HTTP opens, so give it 30 seconds.
4. Check health and the log for failed data steps.
5. Read `framework.release`. If it changed, set `FRAMEWORK` in [bearer-apps.config.mjs](../Scripts/bearer-apps.config.mjs) to it and rerun [deploy-bearer-apps.mjs](../Scripts/deploy-bearer-apps.mjs), which refuses to deploy against a different framework. It redeploys the source and leaves linked accounts alone.
6. Run one read through each app, then record the version on the front page.

## Adding an MCP Server

A server that needs no sign-in or offers OAuth: `tools.executor.apps.importCustom({ body: { source: { kind: "mcp", name, url } } })`. The app's name decides its slug. For OAuth, connect the account afterwards from the app's **Accounts** tab while signed in to the dashboard.

A server behind a static bearer token: add a row to `bearer-apps.config.mjs` with the server, the provider host and the password-manager item, then run the deploy script for that slug with `EXECUTOR_PAT` and `TOKEN_<SLUG>` injected from my password manager.

A server at a private address works from app code because of `EXECUTOR_APPS_ALLOW_PRIVATE_FETCH`. Adding one by URL, or signing in to one with OAuth, also needs its exact origin in `EXECUTOR_URL_ALLOW_HTTP_ORIGINS`, followed by a container recreate.

## Rotating a Bearer Token

Change the token at its server and in my password manager, then replace the account's credentials from the app's **Accounts** tab with **Update credentials**. The account keeps its ID, so the app link survives.

## Clients

A client needs the server once, then a browser sign-in:

```bash
claude mcp add --transport http --scope user executor https://executor.alphasecunited.com/mcp   # then /mcp in a session
codex mcp add executor --url https://executor.alphasecunited.com/mcp && codex mcp login executor
```

The dashboard's **Connected agents** lists every approved client and revokes a grant. A personal access token from **Account settings, Tokens** works as the bearer token for a script or a client that cannot sign in.

## Restarting and Stopping

```bash
cd /opt/docker/executor-v2
docker compose restart executor
docker compose stop
docker compose up -d
```

None of these removes the data directory. A restart ends every MCP session, and a program running at that moment cannot resume.

## Recovery

The durable state is the whole `data` directory together. Its key files are tied to the database: a missing or replaced `encryption.key` makes every stored credential unreadable, and startup refuses a missing key for an existing database. I keep no backup. If the directory is lost I rebuild: start a fresh container with empty directories owned by UID 1000, claim the owner account with `POST /api/auth/self-host/setup` using my standard application account and organization name `AlphaSec United`, create a new personal access token, rerun the deploy script for the bearer apps, re-add the URL apps, reconnect the three OAuth accounts in the browser, and sign in each client again.
