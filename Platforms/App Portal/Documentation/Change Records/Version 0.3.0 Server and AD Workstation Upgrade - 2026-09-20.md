# Version 0.3.0 Server and AD Workstation Upgrade

**Created:** 2026-09-20  
**Last updated:** 2026-09-20

I upgraded the App Portal server on `docker-main` and the client on the AD test workstation `HQ-WS001` to [v0.3.0](https://github.com/Duresa7/app-portal/releases/tag/v0.3.0). Verification finished shortly before 1:00 AM Eastern on September 20. The server now uses SQLite and exposes the catalog, device, install-history, software-request and enrollment-key admin pages.

## Deployment and migration

The first attempt had fast-forwarded `/opt/docker/app-portal` to `53e7d11`, downloaded the release image and passed `deploy/smoke-test.sh` against a temporary container using fake Action1 responses. It stopped before recreating production. I checked the live state before continuing: `app-portal-server:local` was still healthy, and the volume held two devices and five successful installs in JSON.

I added `APP_PORTAL_VERSION=0.3.0` to `deploy/.env`, retaining `APP_PORTAL_BIND=192.168.40.35:3004`, then ran `docker compose -f deploy/compose.yaml up -d --no-build --pull never`. Compose recreated only `app-portal`. The release image is `ghcr.io/duresa7/app-portal-server:0.3.0`, digest `sha256:7d459a1539969d507306af0649c5313d1b1904ee725563f764c813df3a6c118f`.

The server applied seven schema migrations and imported five catalog apps, both device registrations and all five install records into `/app/data/app-portal.db` on `deploy_app-portal-data`. My first read-only database check used `portal.db` and failed with `sqlite3.OperationalError: unable to open database file`; listing the volume established the correct filename, and the corrected check returned `integrity_check = ok`. The container itself had already started successfully.

I compared both token hashes and every legacy install's identifier, device, app identifier, app name, state and percentage with SQLite. All matched. I then removed the imported `devices.json` and `installs.json`, leaving SQLite as the state store. No snapshot or backup was created. The mounted catalog JSON remains a seed for an empty database; subsequent catalog edits belong in SQLite through the admin pages or catalog CLI.

The live Compose file, `.env` settings and database catalog export are captured under [Configuration](../../Configuration/). `compose.env` is the reference copy of the host's `deploy/.env`.

## Workstation and admin login

I started the existing `App Portal Updater` task on `HQ-WS001` through the Proxmox guest agent on `grey_server`, VM 310. No App Portal client was running there. Its log recorded the v0.3.0 download and SHA-256 verification at 12:43:31 AM Eastern, then installation over 0.2.1 at 12:43:33 AM. The executable changed from `0.2.1.0` to `0.3.0.0`; the task returned 0. A second run reported `UpToDate` at 12:46:29 AM, installed and latest versions both `0.3.0`, no staged version and task state `Ready`. I confirmed `.previous`, `.update` and `.staged` were absent inside the installation directory afterward.

I created `portal-admin` and saved its login in the vault item *<REDACTED_CREDENTIAL_ITEM_NAME>*, with the URL `https://appportal.alphasecunited.com/admin/login`. I verified the saved password by readback before creating the server account. The transfer used a temporary RSA public key and encrypted output; the private key and temporary password files were removed afterward. The first vault-create call succeeded, but parsing its human-readable response as JSON failed. I checked the item list, confirmed exactly one matching item and verified its password instead of creating another.

I signed in through the HTTPS login form, opened all six admin pages, tested API session creation and revocation, and signed out of the browser session. The checks used the saved credential without printing it.

## Verification

| Check | Observed result |
|---|---|
| Released image smoke test, recovered from the first attempt | Passed health, Docker healthcheck, catalog import/export/edit, device authentication, simulated install, admin authentication and software-request approval paths |
| Production Docker state after migration and cleanup | Image `ghcr.io/duresa7/app-portal-server:0.3.0`, running, healthy |
| HTTPS health | HTTP 200, `{"status":"ok"}` |
| SQLite | Integrity `ok`; seven migrations, five catalog apps, two devices, five installs |
| Device tokens and legacy history | Both hashes preserved; all five compared install records matched |
| Live catalog verification | Chrome `153.0.8010.53`, Firefox `156.0`, 7-Zip `26.03.00.0`, VLC `3.0.23`, VS Code `1.138.0`; all package identifiers resolved through Action1 |
| `HQ-WS001` | Client `0.3.0.0`, updater `UpToDate`, task exit 0, Action1 endpoint `Connected`; authenticated HTTPS reads returned five apps, one install and zero software requests |
| `ObiPC` compatibility | Client `0.2.1.0`, Action1 endpoint `Connected`; authenticated HTTPS reads returned five apps, four installs and zero software requests |
| Anonymous access | `/admin` redirected with HTTP 302; `/api/v1/catalog` returned 401 |
| Admin browser pages | `/admin`, `/admin/catalog`, `/admin/devices`, `/admin/installs`, `/admin/requests`, `/admin/keys` all returned 200 after sign-in |
| Admin sessions | API login 200, API logout 204, browser logout 302 |

The first workstation summary used incorrect response-property names and counted wrapped PowerShell arrays, producing null names and counts of one. I corrected the summary to use the published API properties and the returned arrays; the table records the corrected observations.

I retained the configuration exports, but not full per-command transcripts for these steps. The table records the observed results. The earlier smoke-test output was recovered from the interrupted work rather than rerun against production.

## Open

- `ObiPC` still has a `0.2.1.0` client open. I left that session intact. Its last updater status predates this release and reports `0.2.1`; it needs a new update check and client restart to receive the new interface.
- I verified live authentication, catalog resolution, history and request reads, plus the admin pages. I did not launch the updated desktop UI interactively or submit a new production install or software request during this upgrade.
- The four successful `ObiPC` history records supersede the README's earlier statement that it had no install history. The legacy records do not identify the requesting person, so they do not establish an interactive test by `IK-user`.
- Client enrollment-code exchange and signed releases remain project work. The new admin enrollment-key pages do not by themselves provide the future client enrollment flow.
