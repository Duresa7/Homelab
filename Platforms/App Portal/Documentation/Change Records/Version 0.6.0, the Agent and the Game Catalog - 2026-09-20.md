# Version 0.6.0, the Agent and the Game Catalog

**Created:** 2026-09-20  
**Last updated:** 2026-09-20

App Portal shipped v0.5.0 at 4:04 PM and v0.6.0 at 6:17 PM on 2026-09-20, which is eleven merged pull requests past the v0.3.0 this deployment was running. The two releases replace the whole client delivery mechanism: the zip archive and its `App Portal Updater` scheduled task are retired, an MSI carrying a `LocalSystem` agent service takes over, and that agent can install software itself through winget or a direct installer instead of handing every install to Action1.

I upgraded the server, moved both PCs onto the MSI, added the five applications `IK-user` asked for, and opened the AppLocker holes those applications need on `ObiPC`. Four of the five install and run for him. VALORANT does not, for reasons that were true before I started.

## The server

`docker-main` now runs `ghcr.io/duresa7/app-portal-server:0.6.0`. I pinned `APP_PORTAL_VERSION=0.6.0` in `deploy/.env`, pulled the released image, stopped the container, copied `app-portal.db` to `/root/app-portal-pre-0.6.0/` as a rollback point, and started it with both `compose.yaml` and `compose.override.yaml`. The container reported healthy six seconds after start and `https://appportal.alphasecunited.com/healthz` answered `{"status":"ok"}` at 6:32 PM.

Eleven migrations applied on first start, 008 through 018: admin source, enrollment, agent jobs, device software, job requester, software account, settings, app requirements, reboot state, prerequisites and uninstall. Only migration 013 drops anything, and what it drops is the `device_software` cache that migration 011 had created minutes earlier in the same start, so nothing that existed before the upgrade was touched. Both device registrations and both administrator accounts came through unchanged.

The `Directory__*` settings staged on 2026-09-20 are no longer inert. The server logs `OpenLDAP will validate directory certificates against /app/config/dc-certs.pem` at every start, which is 0.6.0 reading the configuration that 0.3.0 ignored. **I did not sign in through the directory to prove the bind end to end tonight**, so that verification still stands at what the [directory sign-in record](Directory%20Sign-In%20for%20the%20Portal%20-%202026-09-20.md) proved against a locally built server.

The pre-upgrade database copy is still at `/root/app-portal-pre-0.6.0/` and comes off once this has run for a few days.

## Both PCs onto the MSI

A zip installation cannot reach 0.6.0 by itself. The updater it carries swaps files by renaming them, and an MSI does not arrive that way, so each machine needed the MSI pushed once. The MSI keeps the existing `client.json`, so neither device enrolled again or changed its token, and the agent deletes the leftover scheduled task the first time it starts.

`HQ-WS001` went from the 0.3.0 zip to the MSI between 6:34 and 6:35 PM, `msiexec` exit 0. `ObiPC` turned out to be running **0.5.0**, not the 0.3.0 the last record left it on: its old updater had taken it as far as the last release that still published a client zip, and then had nowhere further to go. It took the MSI at 6:52 PM, also exit 0.

After both:

| Check | HQ-WS001 | ObiPC |
|---|---|---|
| `AppPortal.exe` file version | 0.6.0.0 | 0.6.0.0 |
| `AppPortal.Agent.exe` file version | 0.6.0.0 | 0.6.0.0 |
| `AppPortalAgent` service | Running, Automatic, `LocalSystem` | Running |
| `App Portal Updater` task | gone | gone |
| `client.json` token | kept | kept |
| `enroll.json` | absent, so no second enrollment | absent |
| Device row `has_agent` / `agent_version` | 1 / 0.6.0 | 1 / 0.6.0 |

Two things the MSI does not clean up, because they were never its files, and I removed both by hand on each machine: `AppPortal.Updater.exe` in `%ProgramFiles%\App Portal`, and the `AppPortalClient` uninstall registry key the zip installer wrote. That key mattered. Its uninstall string still pointed at `Uninstall-AppPortalClient.ps1`, which deletes the Program Files directory, so anyone using Apps & Features to remove the stale entry would have taken the MSI installation out with it. Each machine now shows one entry, `App Portal 0.6.0`.

On `ObiPC` the MSI would not run from an SSH session. `Start-Process msiexec` returned immediately having done nothing, leaving a two-byte log, because the SSH Manager gateway wraps every command in `powershell -NoProfile -OutputFormat Text -EncodedCommand` and the argument array did not survive it. A one-shot SYSTEM scheduled task running `msiexec /i ... /qn /norestart /l*v` installed it with `LastTaskResult` 0. I removed the task afterwards.

## The five applications

`IK-user` asked for Steam, Spotify, Discord, Roblox and VALORANT. Action1's Software Repository carries none of them, which `packages search` confirmed for all five, so every one of them has to run on the agent engine rather than Action1.

I took the package identifiers from the `microsoft/winget-pkgs` manifests rather than guessing them: `Valve.Steam`, `Spotify.Spotify`, `Discord.Discord`, `Roblox.Roblox` and `RiotGames.Valorant.NA`. The manifests also settled the scope question, and the answer is the reason for most of the work below: Steam installs machine-wide, and Spotify, Discord, Roblox and VALORANT all install into the profile of the person who asks.

Four of the five then moved off winget and onto direct installers, for two separate reasons covered below. Each direct entry pins the vendor's own installer URL, its SHA-256 and its size, all three taken from the winget manifest and all three verified against the file I downloaded. The catalog now holds ten applications and `catalog verify` resolves every one; the export is in [Configuration/catalog.json](../../Configuration/catalog.json).

## Why a per-user install collides with the ObiPC lockdown

The agent runs a per-user install in the session of the person who asked, through `CreateProcessAsUser` with their own token. AppLocker judges that process as them. `IK-user` has no allow rule of his own anywhere in the Exe collection, so what runs for him is `%WINDIR%` and the two Program Files trees, which is exactly what the 2026-09-18 lockdown intended. An installer downloaded to a temporary directory is not in any of those, and neither is the application it writes into his profile.

His account also carries a packaged-app deny on `Microsoft.DesktopAppInstaller`, written so that winget could not install a signed package for him. That deny does its job: the first Spotify attempt at 6:56 PM ran `winget install --id Spotify.Spotify --exact --scope user` in his session and exited `-1073741790`, which is `0xC0000022`, access denied. The theory and the evidence agree.

So per-user applications on `ObiPC` needed two changes, and the second exists to avoid making the first one bigger:

- **Publisher allow rules** for Spotify AB, Discord Inc., Roblox Corporation and Riot Games, added to his group. A publisher rule follows the signature rather than the location, so it covers the installer running from a temporary directory and the application running out of his profile, and it keeps working when those applications update themselves. Details and verification are in the [AppLocker record](../../../Active%20Directory/Documentation/Change%20Records/ObiPC%20Publisher%20Allows%20-%202026-09-20.md).
- **Direct installers instead of winget** for those applications, so the App Installer deny stays exactly as it was. Allowing him winget would have reopened the path the lockdown closed, because the Appx collection allows every signed packaged app for `Everyone` and winget installs signed packaged apps without elevation.

The cost of the direct entries is that a pinned URL and hash go stale when a vendor ships a new build. A stale entry fails a **new** install with a hash mismatch; it does not affect an installation already on a machine, because all four of these applications update themselves.

## Two defects in 0.6.0

**A progress report that moves backwards kills the job, and the job then repeats without limit.** `AgentJobStore.Update` refuses an update matching `NOT (state = 'installing' AND @state = 'downloading')` and the endpoint turns that refusal into HTTP 409. The agent derives its progress state from the installer's own output, calling anything that starts with `Downloading` a download and everything else an install, so winget's ordinary output order sets `installing` from `Found Steam [Valve.Steam] Version 2.10.91.91` and then `downloading` from `Downloading https://cdn.akamai.steamstatic.com/...`. The agent treats the 409 as fatal, abandons the run, and picks the job up again five seconds later.

The proxy access log is unambiguous. Per attempt: `GET /api/v1/agent/jobs?wait=25` 200, then progress 204, 204, **409**, 204, then the next attempt five seconds later. One 409 per attempt, for attempts 1 through 135, on one Steam job. The `attempt < 3 THEN 'queued' ELSE 'failed'` cap in `RequeueExpired` never fired, because the job is not expiring, so a second defect is that the retry cap does not hold on this path. The install sat at `Waiting for the agent to resume` the whole time, and because the server issues one job to a device at a time, everything queued behind it waited too.

I did not patch the product tonight. I worked around it by putting Steam on a direct installer as well, whose progress output runs in one direction, and cleared the stuck job by hand: `agent_jobs` row to `failed` and its install row to `Failed` with the reason written into `detail`. That hand edit is the only write I made to the database outside the application.

## What installs, and what does not

Everything below is for `IK-user` on `ObiPC`, with him signed in and clicking the buttons himself.

| Application | Engine, scope | Result |
|---|---|---|
| Spotify | direct, user | Succeeded 7:14:14 PM, requested 7:08:18 PM |
| Roblox | direct, user | Succeeded 7:17:07 PM |
| Discord | direct, user | Succeeded 7:17:17 PM |
| Steam | direct, machine | Succeeded 7:17:38 PM |
| VALORANT | winget, user | Failed 7:17:40 PM, `winget failed with exit code -1073741790` |

Confirmed on the machine rather than from the portal: `steam.exe` under `C:\Program Files (x86)\Steam`, an Apps & Features entry named `Steam`, and `Spotify.exe`, Discord's `Update.exe` and `RobloxPlayerBeta.exe` all present under his profile. `C:\Riot Games` does not exist.

VALORANT fails for two reasons that stack, and neither is something the portal can fix. Its winget package is the only identifier Riot publishes, so it runs through the engine his account is denied; and the installer needs administrator rights to put the Vanguard anti-cheat driver in place, which he does not have and is not getting. The entry stays in the catalog by decision so he can ask for it and get a clear answer rather than wonder why it is missing. Its `requirements` text now opens with "Ask an administrator to install this one" and explains why, because the card was otherwise showing him `winget failed with exit code -1073741790`.

Vanguard's hardware prerequisites are already met on this machine: `Confirm-SecureBootUEFI` returns True and the TPM reports present, ready and version 2.0.

**The installer is staged for an administrator at the keyboard.** `C:\Staged\VALORANT\VALORANT-Installer-NA.exe`, 75,182,824 bytes, SHA-256 `0406312AEB92005E7E65C990A5AE4D8406CEC2EF5CE095D1797D50A16A35E45F`, which matches the `microsoft/winget-pkgs` manifest. Its Authenticode signature is Valid and signed by Riot Games, Inc., and its AppLocker publisher string is the one rule `...143` allows. `C:\Staged` has inheritance disabled and grants only `BUILTIN\Administrators` and `NT AUTHORITY\SYSTEM`, so `IK-user` can neither see nor run it. Riot installs the game to `C:\Riot Games` and Vanguard to Program Files, both machine-wide, so once an administrator has run it and the PC has restarted, the publisher rule is what lets him launch it from his own account.

## Open

- Report both defects to the project and decide whether to fix the server guard, the agent's handling of a 409, or both. The clean fix is for a backwards progress report to be a no-op answered 204 rather than a conflict.
- Re-check the Discord silent switch. `--silent` is the Squirrel convention and the install succeeded, but the winget manifest names no switch at all, so it is the one argument in the four direct entries I did not take from a published source.
- Prove directory sign-in against the released server, which needs one sign-in through `/admin/login` with a member of `APP-AppPortal-Admins`.
- Remove `/root/app-portal-pre-0.6.0/` from `docker-main` once 0.6.0 has run for a few days.
- Decide whether pinned installer hashes get refreshed on a schedule or when an install fails.
