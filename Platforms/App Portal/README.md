# App Portal

**Created:** 2026-09-19  
**Last updated:** 2026-09-20

App Portal is my own self-service software catalog for Action1-managed Windows PCs. The person at the keyboard opens a desktop app, picks an approved application, and the Action1 agent installs it as `LocalSystem`. They never need administrator rights, never download an installer, and never touch an API credential.

I built it because `IK-user` on `ObiPC` has no install path of his own by design, and every request currently has to reach me. Action1 announced a Self-Service App Portal on 2025-10-30 but it is still on the "Upcoming release" tab of the public roadmap as of 2026-09-19, and no service release through May 2026 mentions it. If Action1 ships theirs, I compare and probably retire mine.

Source is a separate public repository: [Duresa7/app-portal](https://github.com/Duresa7/app-portal). This folder holds the deployment, not the code.

## Current State

| Item | Current value |
|---|---|
| Deployment status | Server running since 2026-09-19, upgraded to v0.3.0 and verified healthy on 2026-09-20. All five catalog packages resolve against Action1. Both enrolled PCs authenticate over HTTPS. Migrated history contains one successful install for `HQ-WS001` and four for `ObiPC`; the initiating person on the older records is not recorded |
| Compute | Galaxy CT 110 `docker-main`, `192.168.40.35`, VLAN 40 |
| Live path | `/opt/docker/app-portal`, a clone of the public repository |
| Container | `app-portal`, released image `ghcr.io/duresa7/app-portal-server:0.3.0`, `restart: unless-stopped`; verified 2026-09-20 |
| Listener | `192.168.40.35:3004` mapped to container port 8080, reached as `https://appportal.alphasecunited.com` through Nginx Proxy Manager proxy host 32. Clients use the TLS name; the plain port stays for the server's own tooling on `docker-main` |
| Compose project | `/opt/docker/app-portal/deploy/compose.yaml`; `deploy/.env` pins `APP_PORTAL_VERSION=0.3.0` and `APP_PORTAL_BIND=192.168.40.35:3004` |
| Catalog | SQLite is authoritative from v0.3.0; the mounted `deploy/config/catalog.json` seeds an empty database. Five apps: Google Chrome, Mozilla Firefox, 7-Zip, VLC media player, Visual Studio Code. All five verified against the tenant on 2026-09-20; edits are available through `/admin/catalog` |
| Devices | `HQ-WS001` (test VM, VLAN 65) and `ObiPC` (VLAN 60), both enrolled 2026-09-19 and both pointing at the TLS name. Tokens are in the vault items *<REDACTED_CREDENTIAL_ITEM_NAME>* and *<REDACTED_CREDENTIAL_ITEM_NAME>*. Rotate with `device add` for the same name. Action1 lists two `ObiPC` endpoints; the registration names the rebuilt machine enrolled on 2026-09-19, not the pre-rebuild entry from 2026-09-13 |
| State | Named volume `deploy_app-portal-data` at `/app/data`, holding `app-portal.db` and its SQLite WAL files. Seven migrations applied. Both device token hashes and all five install records verified after import; imported JSON files removed on 2026-09-20 |
| Administration | `https://appportal.alphasecunited.com/admin/login`; use the username and password in my replacement App Portal vault login. I switched to that saved login on 2026-09-20 and disabled the original `portal-admin` account. Browser and API sign-in verified; [change record](Documentation/Change%20Records/Administrator%20Login%20Replacement%20-%202026-09-20.md) |
| Secrets on the host | `deploy/server.env`, mode 600, gitignored, rendered from vault references (item *<REDACTED_CREDENTIAL_ITEM_NAME>*: client id, secret, organisation id). Re-render and recreate the container to rotate |
| Client | As verified 2026-09-20: `HQ-WS001` runs 0.3.0.0, updater `UpToDate`, task exit 0. `ObiPC` remains on 0.2.1.0 with a client open; it still authenticates against the upgraded server. The release archive is `AppPortal-client-win-x64.zip` with `SHA256SUMS`. `AppPortal.exe --demo` uses in-memory sample data |

I captured the live [Compose file](Configuration/compose.yaml), its [interpolation settings](Configuration/compose.env) (named `.env` beside Compose on the host), and a [catalog export](Configuration/catalog.json) on 2026-09-20. These are versioned references; the live catalog is in SQLite.

## Directory and agent integration

I checked both workstations and the server on 2026-09-20. `HQ-WS001` and `ObiPC` are joined to `ad.alphasecunited.com`, and the `A1Agent` service is running on both. The portal runs with `Action1__Mode=Live`; both enabled device registrations have Action1 endpoint mappings. All five recorded installs used the `action1` engine and finished `Succeeded`.

Portal administrator accounts are local to its SQLite database. Version 0.3.0 has no AD sign-in, directory synchronization or AD-group catalog assignments. The Windows client sends the current domain and username as a requester label; the device token authenticates the call. Saving a matching username and password in the portal does not connect that account to AD.

The separate App Portal Windows agent is not deployed: neither PC has that service, and both device rows report `has_agent = 0`. The [project roadmap](https://github.com/Duresa7/app-portal/blob/v0.3.0/docs/ROADMAP.md) places automatic enrollment, the agent service and MSI installation in milestone 2 (planned v0.4.0), and agent-driven winget or direct-installer execution in milestone 3 (planned v0.5.0). Version 0.3.0 exposes enrollment-key management but still requires manual device registration and Action1 for installations. Client updates currently use the `App Portal Updater` scheduled task, which was `Ready` on both PCs.

I retained these observations rather than full command transcripts. The live checks read domain membership, service state, container configuration and database integration flags without changing either workstation or the server.

## How a request flows

1. The client reads `%ProgramData%\AppPortal\client.json` for the server address and this device's token, then shows the catalog.
2. Install sends `POST /api/v1/installs {appId}`. The server matches the bearer token to a device record, resolves the package version in the Action1 Software Repository, and starts a `deploy_package` automation scoped to that one endpoint.
3. The server polls the automation's endpoint result and records Queued, Running, Succeeded, Failed or Cancelled.
4. Installed software comes from Action1's inventory for that endpoint, matched back to catalog entries.

The Action1 API credential exists only in `server.env` on `docker-main`. A device token authorises installs of catalog apps on that device's own endpoint and nothing else, so a token lifted from a workstation cannot reach another machine or install anything outside the catalog.

## Why it fits the ObiPC lockdown

The client installs to `%ProgramFiles%\App Portal`, which the `ObiPC` AppLocker allowlist already covers through its `Everyone` Program Files rule, so no new rule is needed. The client never runs an installer itself; the Action1 agent does that as `LocalSystem`, which AppLocker does not evaluate. That keeps the property I set on 2026-09-18: Action1 remains the only install path for `IK-user`.

## How the client stays current

The install script registers a scheduled task, **App Portal Updater**, that runs `AppPortal.Updater.exe` as `SYSTEM` after boot, after logon, daily, and on request. It reads the newest GitHub release, verifies the archive against the release's `SHA256SUMS`, stages it inside Program Files and swaps it in by renaming, so a running client is never killed and the updater can replace itself. The client shows an *Update now* banner, then *Restart to update* once a build is staged. The trust boundary is the GitHub account: the releases are unsigned, and signing is the open hardening item. The full design is in the [record](Documentation/Change%20Records/Credential%2C%20Catalog%20Verification%20and%20Self-Update%20-%202026-09-19.md).

## Records

- [Administrator Login Replacement - 2026-09-20](Documentation/Change%20Records/Administrator%20Login%20Replacement%20-%202026-09-20.md): switch to my replacement vault login and disable the original administrator.
- [Version 0.3.0 Server and AD Workstation Upgrade - 2026-09-20](Documentation/Change%20Records/Version%200.3.0%20Server%20and%20AD%20Workstation%20Upgrade%20-%202026-09-20.md): released Docker image, SQLite migration, admin login, workstation update and verification.
- [Server Deployment on docker-main - 2026-09-19](Documentation/Change%20Records/Server%20Deployment%20on%20docker-main%20-%202026-09-19.md): first deployment, the two defects the deployment exposed, and the verification results.
- [Credential, Catalog Verification and Self-Update - 2026-09-19](Documentation/Change%20Records/Credential%2C%20Catalog%20Verification%20and%20Self-Update%20-%202026-09-19.md): the API credential going live, the empty-body crash the first live call found, the corrected package identifiers, the self-updating client shipped as v0.2.0, and the first real install by a standard user.
- [Internal HTTPS, ObiPC Enrollment and the First Self-Update - 2026-09-19](Documentation/Change%20Records/Internal%20HTTPS%2C%20ObiPC%20Enrollment%20and%20the%20First%20Self-Update%20-%202026-09-19.md): v0.2.1 replacing a running client, the proxy host and certificate, retiring the plain-HTTP firewall allow, and putting the client on `ObiPC`.

## Related

- [Action1](../Action1/README.md) is the management plane this depends on entirely.
- [ObiPC Recovery and Settings Lockdown - 2026-09-18](../Active%20Directory/Documentation/Change%20Records/ObiPC%20Recovery%20and%20Settings%20Lockdown%20-%202026-09-18.md) is why `IK-user` has no other install path.
