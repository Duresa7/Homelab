# App Portal

**Created:** 2026-09-19  
**Last updated:** 2026-09-19

App Portal is my own self-service software catalog for Action1-managed Windows PCs. The person at the keyboard opens a desktop app, picks an approved application, and the Action1 agent installs it as `LocalSystem`. They never need administrator rights, never download an installer, and never touch an API credential.

I built it because `IK-user` on `ObiPC` has no install path of his own by design, and every request currently has to reach me. Action1 announced a Self-Service App Portal on 2025-10-30 but it is still on the "Upcoming release" tab of the public roadmap as of 2026-09-19, and no service release through May 2026 mentions it. If Action1 ships theirs, I compare and probably retire mine.

Source is a separate public repository: [Duresa7/app-portal](https://github.com/Duresa7/app-portal). This folder holds the deployment, not the code.

## Current State

| Item | Current value |
|---|---|
| Deployment status | Server running and healthy on `docker-main` since 2026-09-19. Not yet usable: the Action1 API credential does not exist, so every install attempt answers HTTP 502 by design |
| Compute | Galaxy CT 110 `docker-main`, `192.168.40.35`, VLAN 40 |
| Live path | `/opt/docker/app-portal`, a clone of the public repository |
| Container | `app-portal`, image `app-portal-server:local`, 220 MB, `restart: unless-stopped` |
| Listener | `192.168.40.35:3004` mapped to container port 8080. Plain HTTP on the LAN; TLS is an open item |
| Compose project | `/opt/docker/app-portal/deploy/compose.yaml` |
| Catalog | `deploy/config/catalog.json`, mounted read-only, five apps: Google Chrome, Mozilla Firefox, 7-Zip, VLC media player, Visual Studio Code. Package identifiers are unverified placeholders except Chrome and 7-Zip |
| State | Named volume `deploy_app-portal-data` at `/app/data`, holding `devices.json` and `installs.json` |
| Secrets on the host | `deploy/server.env`, mode 600, gitignored. `Action1__ClientId` and `Action1__ClientSecret` are empty until the credential exists |
| Client | Avalonia desktop app for Windows, published by the repository's CI as `AppPortal-client-win-x64.zip`, currently release v0.1.1. Not deployed to any machine yet. `AppPortal.exe --demo` runs the whole interface from in-memory sample data with no server, which is how to look at it on a machine that is not enrolled |

## How a request flows

1. The client reads `%ProgramData%\AppPortal\client.json` for the server address and this device's token, then shows the catalog.
2. Install sends `POST /api/v1/installs {appId}`. The server matches the bearer token to a device record, resolves the package version in the Action1 Software Repository, and starts a `deploy_package` automation scoped to that one endpoint.
3. The server polls the automation's endpoint result and records Queued, Running, Succeeded, Failed or Cancelled.
4. Installed software comes from Action1's inventory for that endpoint, matched back to catalog entries.

The Action1 API credential exists only in `server.env` on `docker-main`. A device token authorises installs of catalog apps on that device's own endpoint and nothing else, so a token lifted from a workstation cannot reach another machine or install anything outside the catalog.

## Why it fits the ObiPC lockdown

The client installs to `%ProgramFiles%\App Portal`, which the `ObiPC` AppLocker allowlist already covers through its `Everyone` Program Files rule, so no new rule is needed. The client never runs an installer itself; the Action1 agent does that as `LocalSystem`, which AppLocker does not evaluate. That keeps the property I set on 2026-09-18: Action1 remains the only install path for `IK-user`.

## Records

- [Server Deployment on docker-main - 2026-09-19](Documentation/Change%20Records/Server%20Deployment%20on%20docker-main%20-%202026-09-19.md): first deployment, the two defects the deployment exposed, and the verification results.

## Related

- [Action1](../Action1/README.md) is the management plane this depends on entirely.
- [ObiPC Recovery and Settings Lockdown - 2026-09-18](../Active%20Directory/Documentation/Change%20Records/ObiPC%20Recovery%20and%20Settings%20Lockdown%20-%202026-09-18.md) is why `IK-user` has no other install path.
