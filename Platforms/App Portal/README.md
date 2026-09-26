# App Portal

**Created:** 2026-09-19  
**Last updated:** 2026-09-25

App Portal is my own self-service software catalog for Windows PCs. The person at the keyboard picks an approved application in a desktop app, and it installs as `LocalSystem` through Action1 or the portal's own agent, with no administrator rights and no installer download. Source is a separate public repository, [Duresa7/app-portal](https://github.com/Duresa7/app-portal); this folder holds the deployment. How installs work is in [Architecture](Documentation/Architecture.md).

## Current State

| Item | Current value |
|---|---|
| Server | `app-portal` container, image `ghcr.io/duresa7/app-portal-server:0.6.0`, running on `docker-main` (CT 110, `192.168.40.35`, VLAN 40), read 2026-09-24 |
| Address | `https://appportal.alphasecunited.com` through Nginx Proxy Manager proxy host 32; listener `192.168.40.35:3004` to container port 8080 |
| Compose | `/opt/docker/app-portal/deploy/compose.yaml` plus `compose.override.yaml` for the controller addresses; project name `deploy`, volume `deploy_app-portal-data` |
| Catalog | Ten applications. Chrome, Firefox, 7-Zip, VLC and VS Code on the `action1` engine; Steam, Spotify, Discord, Roblox and VALORANT on the `agent` engine. VALORANT needs an administrator at the keyboard |
| Devices | `HQ-WS001` and `ObiPC`, enrolled 2026-09-19, both on client and agent 0.6.0.0 on 2026-09-20 |
| ObiPC client | The MSI log recorded the App Portal 0.8.0 installation at 12:34:01 PM on 2026-09-23; that night the agent binary read 0.8.0.0 and the service was running. UI binary not rechecked. `IK-user`, the account the portal serves there, was disabled on 2026-09-23. ObiPC was unreachable on 2026-09-24 |
| HQ-WS001 client | Not rechecked since 2026-09-20. VM 310 was stopped on 2026-09-24 |
| Administration | `/admin/login` with the local `dkadi` administrator. Directory sign-in is configured but not yet proven against the released server |
| Secrets | `deploy/server.env` on the host, mode 600, rendered from the Action1 API item in my password manager. Each device token lives in that device's own device-token item |

I captured the [Compose file](Configuration/compose.yaml), its [interpolation settings](Configuration/compose.env) (the host's `deploy/.env`) and a [catalog export](Configuration/catalog.json) on 2026-09-20. On 2026-09-25 I set the version line in `compose.env` to 0.6.0, matching the pin in the 0.6.0 record and the running image. The live catalog is in SQLite.

## Open

- The pre-upgrade database copy at `/root/app-portal-pre-0.6.0/` on `docker-main` has no recorded removal.
- No record says the two 0.6.0 agent-job defects were reported or fixed; see the [0.6.0 record](Documentation/Change%20Records/Version%200.6.0%2C%20the%20Agent%20and%20the%20Game%20Catalog%20-%202026-09-20.md).
- The 0.8.0 agent logged 132 warnings containing `404` on ObiPC on 2026-09-23; see the [event review](../../Security/Assessments/ObiPC%20Event%20Review%20-%202026-09-23.md).
- Releases are unsigned.

## Records

- [ObiPC Event Review - 2026-09-23](../../Security/Assessments/ObiPC%20Event%20Review%20-%202026-09-23.md)
- [Version 0.6.0, the Agent and the Game Catalog - 2026-09-20](Documentation/Change%20Records/Version%200.6.0%2C%20the%20Agent%20and%20the%20Game%20Catalog%20-%202026-09-20.md)
- [Directory Sign-In for the Portal - 2026-09-20](Documentation/Change%20Records/Directory%20Sign-In%20for%20the%20Portal%20-%202026-09-20.md)
- [Administrator Login Replacement - 2026-09-20](Documentation/Change%20Records/Administrator%20Login%20Replacement%20-%202026-09-20.md)
- [Version 0.3.0 Server and AD Workstation Upgrade - 2026-09-20](Documentation/Change%20Records/Version%200.3.0%20Server%20and%20AD%20Workstation%20Upgrade%20-%202026-09-20.md)
- [Internal HTTPS, ObiPC Enrollment and the First Self-Update - 2026-09-19](Documentation/Change%20Records/Internal%20HTTPS%2C%20ObiPC%20Enrollment%20and%20the%20First%20Self-Update%20-%202026-09-19.md)
- [Credential, Catalog Verification and Self-Update - 2026-09-19](Documentation/Change%20Records/Credential%2C%20Catalog%20Verification%20and%20Self-Update%20-%202026-09-19.md)
- [Server Deployment on docker-main - 2026-09-19](Documentation/Change%20Records/Server%20Deployment%20on%20docker-main%20-%202026-09-19.md)

## Related

- [Action1](../Action1/README.md), the management plane the `action1` engine depends on.
- [ObiPC Recovery and Settings Lockdown - 2026-09-18](../Active%20Directory/Documentation/Change%20Records/ObiPC%20Recovery%20and%20Settings%20Lockdown%20-%202026-09-18.md), why `IK-user` had no other install path.
