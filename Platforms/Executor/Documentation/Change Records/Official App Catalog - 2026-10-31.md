# Official App Catalog

**Created:** 2026-10-31  
**Last updated:** 2026-10-31  
**Change date:** 2026-10-31  
**Status:** Complete.

**Apps → Add app → Browse app catalog** listed only the built-in Executor app. I set `EXECUTOR_CATALOG_URL` so it lists Executor's official apps.

## Cause

Executor 2 reads its official apps from a static feed: an `index.json` listing each app, with each app's source at `apps/<id>.json` beside it. The desktop app and CLI default to `https://catalog.executor.sh/index.json`. The self-host build has no default. With the variable unset, the server's catalog source returns an empty list and the server adds only its own Executor entry. The [self-host docs](https://executor.sh/docs/run/self-host) say the same: "Without it, Add app lists only the built-in Executor app." The [Executor 2 migration](Executor%202%20Migration%20-%202026-10-31.md) never set it, because every app there was deployed by script or added by URL.

Before the change, `organization.catalog` returned one entry, `https://executor.alphasecunited.com/openapi.json`. From `docker-blue`, `https://catalog.executor.sh/index.json` returned HTTP 200 with no redirect and 1,840 apps. The server does not follow redirects for the feed.

`appManagement.catalog`, which lists community-published apps from `api.executor.sh`, was unaffected and returned 37 listings.

## Change

1. I added `EXECUTOR_CATALOG_URL: https://catalog.executor.sh/index.json` to the [Compose reference](../../Configuration/docker-compose.yml). `docker compose config -q` passed on `docker-blue`.
2. I installed it as `/opt/docker/executor-v2/docker-compose.yml`, root `0644`. The live file and the reference both hash `e7220f77…` (2,069 bytes), up from `81f831df…`.
3. I added the same key to Dockhand's copy at `/opt/docker/dockhand/stacks/imported/docker_blue/executor-v2/compose.yaml` on `docker-main`, with the environment keys kept in sorted order. The file still round-trips through `json.dumps(indent=2)` and stays root `0600`. It went from `dc72eb20…` to `3d00e148…`.
4. `docker compose up -d --pull never` recreated `executor-v2` on the same pinned image. It reported healthy within seconds, and `/health` returned `{"status":"ok"}`. The log had no errors.

The feed is a public HTTPS origin, so `EXECUTOR_URL_ALLOW_HTTP_ORIGINS` needed no entry. Apps installed from it run with `EXECUTOR_APPS_ALLOW_PRIVATE_FETCH=true` like every other app, so each one can reach the lab.

## Verification

- `organization.catalog` with `limit` 1000 returned 1,000 entries, the cap: the built-in Executor app first, then `gmail`, `google-calendar`, `google-drive`, `outlook` and `twitter`. A search for `gmail` returned `@executor.sh/gmail` (OAuth) and `@executor.sh/bigmailer` (secrets).
- Tool counts after the recreate matched the [runbook](../Runbook.md): `ssh` 15, `unifi` 5, `wazuh` 41. `validate_wazuh_connection` reported `connected`.
- The `cloudflare` app was no longer installed. I had removed it myself earlier the same day, so the recreate did not cause it.
