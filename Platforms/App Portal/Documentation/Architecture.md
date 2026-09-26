# App Portal Architecture

**Created:** 2026-09-25  
**Last updated:** 2026-09-25

How App Portal installs software, why that fits the ObiPC lockdown, and how the client keeps itself current. The deployment facts are in the [README](../README.md). This text moved out of the README on 2026-09-25 and describes the 0.6.0 server with the MSI client.

## Two install engines

**action1** hands the install to an Action1 automation. That is how the portal started, and the five original applications still use it.

**agent** is the `AppPortalAgent` service the MSI installs on each PC. It runs as `LocalSystem`, installs a winget package or a direct installer the catalog names, checks the installer's SHA-256, and runs it. It can install into one person's profile when that is the only place the software goes. The server-wide default engine is `action1`. Every install records which engine ran it.

## How a request flows

1. The client reads `%ProgramData%\AppPortal\client.json` for the server address and this device's token, then shows the catalog.
2. Install sends `POST /api/v1/installs {appId}`. The server matches the bearer token to a device record and picks the engine: the catalog entry's own choice, or the device's, or the server default of `action1`.
3. On the `action1` engine the server resolves the package version in the Software Repository, starts a `deploy_package` automation scoped to that one endpoint, and polls its result.
4. On the `agent` engine the server queues a job, the device's agent collects it from `GET /api/v1/agent/jobs`, installs it, and posts progress and a completion back. A per-user package runs in the session of the person who asked, and waits if they are not signed in.
5. Either way the install is recorded as Queued, Running, Succeeded, Failed or Cancelled. Installed software comes back from Action1's inventory or the agent's own sweep.

The client sends the signed-in Windows account as `X-AppPortal-User: DOMAIN\user`. The server stores it on the install row, and `/admin/installs` can filter by it. The header is informational. The device token is what authenticates the call.

The Action1 API credential exists only in `server.env` on `docker-main`. A device token authorises installs of catalog apps on that device's own endpoint and nothing else. A token lifted from a workstation cannot reach another machine or install anything outside the catalog.

## Administrator sign-in

Portal administrators live in the SQLite `admins` table, and `dkadi` is the one enabled account. Directory sign-in shipped in v0.5.0: a member of `APP-AppPortal-Admins` binds over LDAPS and gets an administrator account named `DOMAIN\user`. Local accounts are checked first, so a controller being down cannot lock the portal out. The server reads the `Directory__*` settings (it logs `OpenLDAP will validate directory certificates` at every start), but I have not signed in through the directory against the released server. See [Directory Sign-In for the Portal](Change%20Records/Directory%20Sign-In%20for%20the%20Portal%20-%202026-09-20.md).

## Why it fits the ObiPC lockdown

The client installs to `%ProgramFiles%\App Portal`. The `ObiPC` AppLocker allowlist covers that path through its `Everyone` Program Files rule. Action1 installs land in Program Files too, and the Action1 agent runs them as `LocalSystem`, which AppLocker does not evaluate. A machine-wide agent install such as Steam also runs as `LocalSystem`.

A per-user install is different. The agent runs it through `CreateProcessAsUser` with the person's own token, so AppLocker judges both the installer and the installed application as that person. `IK-user` had no allow rule of his own outside `%WINDIR%` and Program Files. Seven publisher allow rules for his group (Spotify, Discord, Roblox, Riot Games, Ubisoft, NVIDIA and BattlEye) let the profile-installed applications and his games run. A publisher rule follows the signature rather than the directory, so a program he downloads himself still does not run. His packaged-app denies on App Installer, the Microsoft Store, the Store purchase app and the Xbox app are untouched, which is why the portal uses direct installers rather than winget for these applications. The [publisher allow record](../../Active%20Directory/Documentation/Change%20Records/ObiPC%20Publisher%20Allows%20-%202026-09-20.md) holds the reasoning.

## How the client stays current

The agent updates the whole installation, itself included. It asks GitHub for the newest release when the service starts, once a day at a random second in the noon hour, and within ten seconds of a client asking. It downloads a newer release as an MSI, checks it against that release's `SHA256SUMS`, and installs it with `msiexec /qn /norestart` as `LocalSystem` once no client is running. The client's banners read `%ProgramData%\AppPortal\update.json`.

The `App Portal Updater` scheduled task did this job through v0.5.0 and is retired. It swapped files by renaming them, which is not how an MSI arrives, so each machine needed the MSI once. The agent deletes the leftover task the first time it starts, and it did so on both PCs.

A release exists only after the pipeline has run the tests on Linux and Windows, checked the tag against the version in the source, built the MSI and the bootstrapper, installed them on a Windows runner against a fake-mode server, and smoke-tested the server image. The trust boundary is still the GitHub account: releases are unsigned, and signing is the open hardening item.
