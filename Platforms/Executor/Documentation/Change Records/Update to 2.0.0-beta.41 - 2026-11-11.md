# Update to 2.0.0-beta.41

**Created:** 2026-11-11  
**Last updated:** 2026-11-11

On 2026-11-11 I moved Executor 2 on `docker-blue` from 2.0.0-beta.37 to 2.0.0-beta.41, the newest v2 pre-release that evening. It skipped beta.38 (2026-11-09), beta.39 (2026-11-10) and beta.40 (2026-11-11 morning). The `beta` tag on GHCR resolved to the same digest as `2.0.0-beta.41`.

## What changed upstream

Each release's notes are the same install text with no changelog. What changed is in the `.changeset/` notes and the 152 files between the `executor@2.0.0-beta.37` and `executor@2.0.0-beta.41` tags. Most of the diff is in the hosted cloud server and the e2e tests. The parts that reach a self-host install:

- Remote MCP results drop a text block that only repeats `structuredContent` as JSON. Upstream's reason is that the copy doubled the result at every nested MCP hop.
- `EXECUTOR_CATALOG_URL` now defaults to the official feed, `https://catalog.executor.sh/index.json`, on self-host too, and `off` disables it. Before, self-host listed only the built-in app without the variable. My Compose file sets the official URL explicitly, so nothing changed here.
- The connect form says an app's credential check may be wrong when it rejects a credential, lets the credential be added anyway, and offers a fix prompt for the app's check.
- Self-host auth gained a user-removal path that deletes the user's records.
- `oauth.resolve` spans record the credential's purpose, type, account, organization and actor as opaque IDs. OAuth revoke responses return the revoked connection's ID.
- The apps framework went from `0.0.1-beta.120` to `0.0.1-beta.122`.

No file under the storage migrations or any `.sql` file changed between the two tags, so Executor's own data takes no migration.

## Changes

1. I confirmed the live `/opt/docker/executor-v2/docker-compose.yml` matched the [Compose reference](../../Configuration/docker-compose.yml) by SHA-256 (`93355573…b6a499`) before touching it.
2. I resolved the digest from GHCR's manifest endpoint. The same lookup for `2.0.0-beta.37` returned the digest already pinned, which checks the method. I pulled `ghcr.io/usefulsoftwareco/executor-selfhost:2.0.0-beta.41@sha256:712dc482432c918d48a84f80cc79b12125e951f9bb6929efc7b4594e5523c576` while beta.37 kept serving. The pull log ended on that digest.
3. Because every SSH call runs through Executor, I ran the switch as a detached root script. ssh-mcp refuses a command with a line break, so I sent the script base64-encoded on one line and checked its SHA-256 on the host against my local copy before running it. It started at 7:38:12 PM, stopped the container (stopped at 7:38:27 PM), copied `data` (197 MB) to `data.pre-beta41` as a rollback point, swapped the image pin in the Compose file, and ran `docker compose up -d executor` at 7:38:29 PM. The container reported healthy at 7:38:34 PM. The health endpoint answered 200 from `ubuntu-dev` at 7:38:32 PM.
4. I updated the [Compose reference](../../Configuration/docker-compose.yml). Its SHA-256 (`d5f822f7…dcc55ec`) matches the live file.
5. After verification I deleted `data.pre-beta41`, the script, the switch log and the pull log from `docker-blue`. The beta.37 image stays on the host for a rollback.

I did not redeploy the four bearer apps. They still run on framework `0.0.1-beta.117`, which beta.41 keeps serving, and [bearer-apps.config.mjs](../../Scripts/bearer-apps.config.mjs) still names that version.

## Verification

- `docker inspect` reports the beta.41 digest, `healthy`, zero restarts. `docker stats` showed 3.08% CPU and 708.6 MiB of the 1.5 GiB limit a minute after start. The log since start had no line matching error, fail, warn, migration or storage outside workerd's `nodejs_compat` notices.
- `framework.release` returns `0.0.1-beta.122`.
- One call per app succeeded: `ssh` `list-connections` listed the 25 profiles with `docker_blue` connected, `unifi` `unifi_list_networks` returned 23 networks in total, `wazuh` `validate_wazuh_connection` reported `connected` to API 4.14.10 on `security-01`, and `cloudflare` `whoami` returned its account without an error.
- `/health` returns `{"status":"ok"}`. An unauthenticated POST to `/mcp` answers 401 with a `WWW-Authenticate: Bearer resource_metadata=...` header. `/.well-known/oauth-authorization-server` returns an issuer, a registration endpoint and `S256`.
- `https://executor.alphasecunited.com/login` answers 200 with the [URL.parse polyfill](Safari%2017%20URL.parse%20Polyfill%20-%202026-11-02.md) as the first element in `<head>`, for both plain and gzip-accepting requests.
- The OAuth-signed-in MCP client that ran these checks kept working across the restart without signing in again.

## Open

- The Compose comment above `EXECUTOR_CATALOG_URL` still says self-host has no default feed. That stopped being true with this build. The setting itself is still correct. I left the comment alone so the reference stays byte-identical to the live file, and will reword both together.
- The bearer apps are two framework releases behind. The runbook's step 5 calls for a redeploy on `0.0.1-beta.122`.

## Rollback

The storage schema did not change, so pinning `2.0.0-beta.37@sha256:23b1f96c4098b48ec8bdf71da76bcd6c656ea7c2d390d96287d82442c39d7230` again and recreating the container should return to the old build. The beta.37 image is still on `docker-blue`.
