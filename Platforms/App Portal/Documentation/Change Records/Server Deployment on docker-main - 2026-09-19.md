# Server Deployment on docker-main - 2026-09-19

**Created:** 2026-09-19  
**Last updated:** 2026-09-19

I built App Portal and deployed its server to `docker-main`. The server runs and passes every check I can make without an Action1 API credential. It cannot install anything yet, and that is the honest state: the credential does not exist.

## Why

`IK-user` on `ObiPC` has had no install path of his own since 2026-09-18, when I removed the `C:\Dev` carve-out so that Action1 is the only way software reaches that machine. That works, but it routes every request through me. A self-service catalog gives him a list I control and a button, without giving him rights.

Action1 announced a Self-Service App Portal on 2025-10-30 and said early 2026. On 2026-09-19 the roadmap card still sits on the "Upcoming release" tab, last updated 2026-09-12, with 147 votes, and no service release through May 2026 "Rockledge" mentions it. So I built one.

## What I built

The source is a separate public repository, [Duresa7/app-portal](https://github.com/Duresa7/app-portal), MIT licensed, with no homelab specifics in it. Two pieces:

- **Server.** ASP.NET Core on .NET 10, a minimal API with five routes. It holds the Action1 API credential, maps device tokens to Action1 endpoint identifiers, resolves Software Repository package versions, starts `deploy_package` automations, and polls their endpoint results. Device tokens are stored as SHA-256 hashes and compared in fixed time; the plaintext is printed once, when the device is registered.
- **Client.** An Avalonia desktop app for Windows that follows the Windows 11 design language: a two-layer NavigationView layout with Mica behind the pane, Fluent 2 colour tokens for light and dark, the Windows type ramp on Segoe UI Variable, and 4px control and 8px container corner radii. It shows the catalog, install progress, the device's inventory, and its request history.

The Action1 request shapes come from the OpenAPI specification Action1 publishes at `app.action1.com/apidocs` and from its PowerShell module, not from guesswork. A deployment is `POST /automations/instances/{orgId}` with a `deploy_package` action naming one package identifier and version, scoped to a single endpoint.

There is an in-memory Action1 stand-in for development and tests, so the whole flow runs without a tenant. Thirteen tests cover token authentication, catalog exposure, the install lifecycle, duplicate and concurrency limits, unresolvable packages, and cross-device isolation. All pass.

## Deployment

| Step | Result |
|---|---|
| Clone | `/opt/docker/app-portal` on `docker-main`, from the public repository |
| Build | `docker compose -f deploy/compose.yaml up -d --build`; image `app-portal-server:local`, 220 MB, built from `mcr.microsoft.com/dotnet/sdk:10.0` and run on `aspnet:10.0` as the non-root `app` user |
| Listener | `192.168.40.35:3004` to container 8080, pinned to that one interface rather than published on all of them |
| Catalog | `deploy/config` mounted read-only |
| State | Named volume `deploy_app-portal-data` on `/app/data` |
| Environment | `deploy/server.env`, mode 600, gitignored. `Action1__Mode=Live`, region `https://app.na-2.action1.com/api/3.0`, credential fields empty |
| Restart policy | `unless-stopped` |
| Health check | In-process, since the ASP.NET runtime image ships no `curl` |

`docker-main` was on Docker 29.8.0 and Compose v5.5.1 with 45 GB free before this, and ports 3004 and 8080 were unused.

## Two defects the deployment exposed

Both were real and both are fixed in the repository, not worked around on the host.

**The listener ignored its configured address.** I put `APP_PORTAL_BIND` in `server.env` and the container published on every interface anyway. Compose interpolates variables from a `.env` file beside the compose file; it does not interpolate from `env_file`, which only sets variables inside the container. The bind address now lives in `deploy/.env` and the credential stays in `server.env`, with both documented.

**Registering a device failed on a read-only file system.** `devices.json` defaulted to the config directory, which I mount read-only on purpose because the catalog is configuration rather than state. `device add` threw `System.IO.IOException: Read-only file system`. The device registry is mutable state and now defaults to the data directory, beside the install history.

## Verification

Run against the container on `docker-main` after the rebuild, on 2026-09-19.

| Check | Result |
|---|---|
| `GET /healthz`, no credentials | HTTP 200 |
| `GET /api/v1/catalog`, no token | HTTP 401 |
| `device add` | Token issued, 47 characters |
| `GET /api/v1/catalog` with that token | 5 apps: Google Chrome, Mozilla Firefox, 7-Zip, VLC media player, Visual Studio Code |
| `POST /api/v1/installs` with that token | HTTP 502, "Action1 API credentials are not configured", which is the correct answer while the credential is absent |
| `device remove` | Removed |
| Container | `Up (healthy)`, `192.168.40.35:3004->8080/tcp` |
| Test suite | 17 passed, 0 failed |

The verification device was created and removed inside a single shell pipeline on the host, so its token never reached a transcript.

## Four defects a review found, and what they would have done

I reviewed the code after the deployment and fixed everything it turned up, with a test for each.

| Defect | What it would have done |
|---|---|
| No lock across the check-then-act in `CreateAsync` | Two overlapping requests both read a snapshot showing nothing in flight, both pass the duplicate and concurrency checks, and both start an Action1 deployment. A client retry after a slow answer was enough to trigger it |
| `Upsert` overwrote a record wholesale | The background poller and every client refresh update the same install from their own snapshots. A slow earlier call landing after a fast later one pushed a finished install back to Running and cleared its completion time |
| `devices.json` written in place with no parse guard | A crash mid-write left a truncated file, and the resulting parse error was thrown out of `Authenticate` on every request to every API route until someone repaired the file by hand |
| The client assumed every response body was JSON | An empty body or an unexpected content type, which a reverse proxy in front of the server can produce, threw out of a timer callback and ended the process |

The fixes are a per-device gate around install creation, a stale-write guard in `Upsert` that also refuses to move a terminal state back to active, a write-then-rename for the device file with the same parse guard the catalog already had, and response-body handling in the client that surfaces a message in the window instead of throwing. The test suite went from 13 to 17. I confirmed the client fix by pointing it at a server that answers HTTP 200 with HTML: it draws an error banner and keeps running.

## What this cannot do yet

The Action1 API credential does not exist. I cannot create it: it is made in the Action1 console under Configuration, API Credentials, which needs an interactive console sign-in. Until it exists and reaches `server.env`, the server serves the catalog and refuses every install with a clear message.

No device is registered, because a device record needs `ObiPC`'s Action1 endpoint identifier, which is read through the same API.

The catalog's package identifiers are placeholders except Google Chrome and 7-Zip, which appear in Action1's own documentation. The server has a `catalog verify` command that resolves every entry against the Software Repository and exits non-zero on a miss; it has never been run against a live tenant.

The listener is plain HTTP on VLAN 40. A device token is a bearer secret, so before a client on another network uses it this belongs behind Nginx Proxy Manager with the shared certificate, the same way the other internal applications are fronted.

## Next steps

1. Create the Action1 API credential in the console with `view_endpoints`, `view_software_repository`, `view_installed_software`, `view_automations` and `run_automations`, and store it in the vault with the organisation identifier.
2. Render `deploy/server.env` from that item with `op inject` and restart the container.
3. Run `catalog verify` and correct the package identifiers it rejects.
4. Add a proxy host so the server is reached over HTTPS rather than port 3004.
5. Register `ObiPC` with `device add`, store the token in the vault, and deploy the client through Action1 with `Install-AppPortalClient.ps1`.
6. Confirm `C:\Program Files\App Portal\AppPortal.exe` tests `Allowed` for `IK-user`'s group before telling him it exists.
