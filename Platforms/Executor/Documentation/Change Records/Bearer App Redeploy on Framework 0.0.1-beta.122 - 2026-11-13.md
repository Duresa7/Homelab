# Bearer App Redeploy on Framework 0.0.1-beta.122

**Created:** 2026-11-13  
**Last updated:** 2026-11-13

On 2026-11-13 I rebuilt the bearer-token apps `ssh`, `unifi` and `wazuh` on apps framework `0.0.1-beta.122`, the release Executor 2.0.0-beta.41 serves. They had run on `0.0.1-beta.117` since the [Executor 2 migration](Executor%202%20Migration%20-%202026-10-31.md), across the [beta.37](Update%20to%202.0.0-beta.37%20-%202026-11-05.md) and [beta.41](Update%20to%202.0.0-beta.41%20-%202026-11-11.md) updates. The same day I reworded the stale catalog comment in the Compose file.

## Before the change

`appManagement.list` showed that `cloudflare` is no longer a bearer app. Since 2026-11-01 that slug has been the official catalog app, copied from `https://catalog.executor.sh/apps/cloudflare.json` (`@executor.sh/cloudflare`), with a user-scoped OAuth account and no `server` requirement. [bearer-apps.config.mjs](../../Scripts/bearer-apps.config.mjs) still listed it, so a run of the deploy script with no slug arguments would have deployed bearer source over the catalog app. The other three apps each had one linked `server` account.

## Changes

1. In `bearer-apps.config.mjs` I set `FRAMEWORK` to `0.0.1-beta.122`, matching `framework.release`.
2. At 1:35:13 AM I ran `node deploy-bearer-apps.mjs ssh unifi wazuh` with the personal access token `Executor API Token - ubuntu-dev agents` injected from my password manager as `EXECUTOR_PAT`. The temporary file that held only the item reference was deleted afterwards. The script exited 0 at 1:35:20 AM:

   ```
   ssh: app app_b51b927d-e42b-4d7a-b4b6-dde73e2351ae deployed dpl_4027fc1e-04c3-4840-82fb-bb27f2f5a775
   ssh: account already linked
   unifi: app app_955ef9be-057a-4db3-820a-b1bdcdf7cd3b deployed dpl_e835d793-b143-43c5-8053-a22d2cbcd317
   unifi: account already linked
   wazuh: app app_9e7ad5cb-69d8-4224-9cdf-fd746d9bddb4 deployed dpl_741a4b63-c6c0-47aa-a45d-4eb6f3daf2ef
   wazuh: account already linked
   ```

   No bearer token was read or submitted, because each app's account was already linked.
3. I removed the `cloudflare` entry from `bearer-apps.config.mjs` and left a comment saying why. The config now lists `ssh`, `unifi` and `wazuh`. The password-manager item `Cloudflare API - executor-mcp` is untouched.
4. I replaced the Compose comment above `EXECUTOR_CATALOG_URL`, which said self-host has no default feed, with one saying the official feed has been the default since 2.0.0-beta.41 and that `off` disables it. The value did not change. I wrote the new file beside the live one on `docker-blue`, confirmed `docker compose config` resolved both files to byte-identical output, then moved it into place as `root:root` mode 0644. The live file and the [Compose reference](../../Configuration/docker-compose.yml) both hash to `5a3728fd…e4fc3844`. The container was not recreated and stayed up and healthy.

## Verification

- Each app's `activeDeployment` is the deployment the script printed.
- Tool counts are unchanged from 2026-10-31: 15 for `ssh`, 5 for `unifi`, 41 for `wazuh`.
- `ssh` ran `hostname` on `docker_blue` and returned `docker-blue`. `unifi` `unifi_list_networks` returned 23 networks in total. `wazuh` `validate_wazuh_connection` reported `connected`.
- `executor-v2` reported `Up 30 hours (healthy)` after the Compose file swap.

## Open

Nothing from this change. The [beta.41 record](Update%20to%202.0.0-beta.41%20-%202026-11-11.md)'s two open items are closed here.
