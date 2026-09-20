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

## What "hooked up to Active Directory" actually means here

The install path now records who asked for the software. From `HQ-WS001`, whose console session is my `DK-user` account, I posted one install of 7-Zip to the HTTPS API with the same `X-AppPortal-User` header the client fills in from the Windows session. The server accepted it, started the Action1 automation against that endpoint, and the record came back `Queued` at 1:43:08 AM Eastern and `Succeeded` at 100 percent at 1:43:30, twenty-one seconds later, stored against `ALPHASEC\DK-user`. 7-Zip was already on the machine, so nothing changed on it. That is the first install in the database carrying a requester; the five migrated ones have `requested_by` empty, which is why they cannot tell me who ran them.

The rest of the directory story is narrower than the name suggests, so it is worth stating plainly. Both workstations are joined to `ad.alphasecunited.com` and both run `A1Agent`. The client reads the signed-in Windows account and sends it as a label only: the device token is what authenticates the call, and the server trusts the label because the PC is managed. The portal's own administrator accounts live in its SQLite database and nowhere else. The enabled one is `dkadi`, the username in my replacement vault login, and no account by that name exists in the forest; a `SamAccountName -eq 'dkadi'` query against `HQ-DC01` returns nothing, across ten user objects. Version 0.3.0 has no LDAP bind, no directory synchronisation and no group-driven catalog assignment, so signing in at `/admin` never reaches a domain controller. Renaming that account after a domain user would change the spelling and nothing else. Real directory sign-in is project work, not configuration.

## ObiPC staged the update behind a running client

I started the `App Portal Updater` task on `ObiPC` at 1:40 AM Eastern. It found 0.3.0, verified the archive and staged it beside the running 0.2.1 client: the task returned 0 and `update.json` reports `Staged`, installed `0.2.1`, latest `0.3.0`, with the message *Close App Portal to finish updating*. `IK-user` was signed in at the console with the client open, so I left his window alone. The swap happens on the next updater run after he closes it, which is the behaviour the staged-and-wait design exists for.

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
| Install requested by a domain account | `POST /api/v1/installs` from `HQ-WS001` carrying the console account: `Queued` 1:43:08 AM, `Succeeded` at 100 percent 1:43:30 AM Eastern, engine `action1`, stored as `ALPHASEC\DK-user`; six install rows now, one attributed |
| Portal administrator accounts | `dkadi` enabled, `portal-admin` disabled; exactly one enabled; no forest account named `dkadi` |
| Administrator sign-in from my workstation | API session 200, `/admin/devices` 200 with that token, logout 204, the revoked token 302, anonymous `/admin` 302 |
| `ObiPC` update check | Task exit 0 at 1:40:44 AM Eastern; `update.json` `Staged`, installed `0.2.1`, latest `0.3.0`, staged `0.3.0`, no `.previous` left behind; client still `0.2.1.0` with the user's window open |
| Release gate on the v0.3.0 tag | Every job in `ci.yml` passed: tag against `Directory.Build.props`, tests on Linux and Windows, the client archive checked and started on a Windows runner, the server image smoke tested, then publish |
| Devices and keys | Both device registrations enabled and last seen within the hour; no enrollment keys issued |

The first workstation summary used incorrect response-property names and counted wrapped PowerShell arrays, producing null names and counts of one. I corrected the summary to use the published API properties and the returned arrays; the table records the corrected observations.

I retained the configuration exports, but not full per-command transcripts for these steps. The table records the observed results. The earlier smoke-test output was recovered from the interrupted work rather than rerun against production.

## Open

- Nobody has pressed Install in the desktop client on `ObiPC`. The staged 0.3.0 client is waiting for `IK-user` to close his 0.2.1 window, and an interactive install by him is still the one link in the chain I have never watched end to end.
- The portal has no Active Directory sign-in. Administrators are local accounts with local passwords, and a domain user cannot sign in to `/admin`. An LDAP bind against `HQ-DC01` and `HQ-DC02`, restricted to a group, is the fix, and it is a feature to build rather than a setting to turn on.
- Client enrollment-code exchange and signed releases remain project work. The admin enrollment-key pages do not by themselves provide the client flow.
- The App Portal agent service is still not deployed: both device rows report `has_agent = 0`, and the agent, automatic enrollment and MSI installation sit in milestone 2 of the project roadmap.
