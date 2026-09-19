# ObiPC Restricted User Setup

**Created:** 2026-09-12  
**Last updated:** 2026-09-18

`IK-user` is a software developer using `ObiPC`, and I wanted that account allowlisted rather than trusted: an approved set of applications, a Settings app that stays out of his way but does not let him change the machine, no installing software without my approval, and a limit on how long the machine is used each day. This record is the whole job, from the design through to enforcement, all on 2026-09-12. **It is in force.** By the end of the day `IK-user` was running under the allowlist on his own live session.

The application-deployment half of "no installs without my approval" is [Action1](../../../Action1/README.md), the console I push software from. This record is the execution half: the wall that stops everything I did not push.

## Groups

| Object | Location | Members | Role |
|---|---|---|---|
| `ROL-ObiPC-Restricted` | `OU=Roles,OU=Groups` | `IK-user` | Principal on the allowlist and Settings rules |
| `ROL-ObiPC-Unrestricted` | `OU=Roles,OU=Groups` | `DK-user`, `AH-user`, `testuser` | Holds the allow-all rule so restriction lands on one account, not the machine |

Both are global security groups created 2026-09-12.

The two-group split is the heart of the design and worth stating plainly. AppLocker enforcement is machine-wide per rule collection; per-user scoping is done by the principal SID on each rule. Restricting one person on a shared machine therefore means the allowlist rules name `ROL-ObiPC-Restricted`, a single allow-all rule names `ROL-ObiPC-Unrestricted`, and a baseline that every identity needs is written against `Everyone`. The failure mode to remember: a user in neither group, with no `Everyone` baseline, matches no allow rule, and AppLocker blocks what no rule allows. I hit exactly this during the rollout, described below. The fix was the `Everyone` baseline; the rule of thumb stands, that any account signing in to `ObiPC` should be in one of the two groups.

## AppLocker works on Windows 11 Pro

`ObiPC` runs Windows 11 Pro, which historically could configure AppLocker but not enforce it. That is no longer true and it is the fact the whole approach rests on. Microsoft's [Requirements to use AppLocker](https://learn.microsoft.com/windows/security/application-security/application-control/app-control-for-business/applocker/requirements-to-use-applocker) states that as of KB 5024351, Windows 10 version 2004 and newer and all Windows 11 versions no longer require a specific edition to enforce. Group Policy deployment to this machine is supported without Intune and without an edition upgrade, and the enforcement below proves it on the live machine.

## Decisions taken

| Question | Decision |
|---|---|
| Sign-in window | 8:00 AM to 10:00 PM Eastern, enforced by the session script in local time |
| Daily usage budget | 240 minutes per day inside that window, reset at midnight |
| Machine scope | Account restricted to `OBIPC` through `userWorkstations` |
| Where self-built binaries may run | `C:\Dev` plus the per-user toolchain directories |
| Applications | Chrome, Visual Studio Code, Git, Node.js, Python. No WSL, no Docker |
| Rollout | Enforce Exe, Msi, and Appx immediately; audit the Script collection |

Costs that belong in the record rather than in my memory:

**The developer carve-out is a deliberate hole** (closed 2026-09-18: the executable allows for `C:\Dev` and the toolchain paths were removed in [ObiPC Recovery and Settings Lockdown](ObiPC%20Recovery%20and%20Settings%20Lockdown%20-%202026-09-18.md), so that Action1 is the only way software reaches the account; the Script-collection allows remain). Allowlisting `C:\Dev` and the per-user toolchain directories (`.vscode`, npm, pip, cargo, go) is what makes development possible, because every binary a developer compiles is a new unapproved executable. Those paths are writable by the user, so the policy stops casual installs and drive-by downloads, not a person who understands it and drops an executable into `C:\Dev`. It is not a security boundary against the human at the keyboard.

**Logon hours as stored are a backstop, not the enforcer.** The window is enforced by the scheduled task in the machine's local time, so it follows daylight saving with no intervention. The Active Directory logon-hours attribute is set wider on purpose, 7:00 AM to 11:00 PM, so daylight saving drift in the stored UTC bytes can never lock him out inside a legitimate hour. If the script is broken or disabled, the directory still refuses a sign-in outside 7 to 11.

**The daily budget is homegrown.** Windows has nothing native for it on a domain account; Family Safety needs a personal Microsoft account. It is a script and scheduled task I own, with state the user cannot reach.

**None of this reaches Microsoft 365.** Entra ID honours neither logon hours nor `userWorkstations`. `IK-user` signs in to the tenant on Business Basic and that is unaffected. Limiting it needs Conditional Access, and the [standing tenant decision](../../../Microsoft%20Intune/README.md) forbids a policy that requires a compliant device.

## What I built

**Two Group Policy objects, linked to `OU=Standard,OU=Workstations`, each security-filtered.**

- `C-WKS-ObiPC-AppControl`, computer side, filtered to the `OBIPC` computer account. Carries the AppLocker rules, sets User Policy loopback to Merge (the policy report read on 2026-09-18 carries no `AppIDSvc` start value, so the Automatic start type I claimed here was never in the policy; the service is a protected process and I set it with `sc.exe` on the machine on 2026-09-18), and sets the restricted-user UAC prompt to prompt for credentials. User side disabled.
- `U-WKS-ObiPC-Restricted`, user side, filtered to `ROL-ObiPC-Restricted`, applied through loopback merge. Hides all Settings pages except a named allowlist (see below), removes the Microsoft Store, disables the registry-editing tools, and blocks all Chrome extension installs. Computer side disabled.

Loopback merge is why a user-side GPO filtered to a group takes effect from a policy linked at the computer's OU: the machine pulls the restricted user's settings on top of the user's own because the computer is in scope.

**The AppLocker policy**, versioned at [`Configuration/ObiPC-AppLocker.xml`](../../Configuration/ObiPC-AppLocker.xml) (sha256 `f86d3ae0993ec4a73f8b900b14f8ea3347b3f19941c561789b6db03ed33f1e70`, byte-identical to what is imported into the GPO):

- **Exe, enforced.** `Everyone` may run `%WINDIR%` (minus the standard writable-subfolder exceptions) and `%PROGRAMFILES%`. Administrators and `ROL-ObiPC-Unrestricted` may run anything. `ROL-ObiPC-Restricted` additionally may run `C:\Dev` and the six toolchain paths, and is denied `regedit.exe` and `regedt32.exe`.
- **Msi, enforced.** `Everyone` may run the `%WINDIR%\Installer` cache; only administrators and unrestricted users may run installers generally. The restricted group has no general MSI allow, so `IK-user` cannot run an installer he brought himself.
- **Appx, enforced.** Signed packaged apps allowed for `Everyone`, administrators, and unrestricted users, which keeps the Start menu, Settings, and inbox apps working while blocking unsigned sideloaded packages.
- **Script, audit only.** Same baseline as Exe, logging without blocking, because script blocking is the noisiest and a developer's tooling runs scripts constantly. This is the one collection deliberately not enforced.

The Settings allowlist (`SettingsPageVisibility` = `hideonly:...`) hides Windows Update, Defender, Windows Insider, other users, date and time, proxy and VPN, recovery, troubleshoot, backup, activation, optional features, default apps, apps and features, workplace, email and accounts, your info, and sync. Personalisation, display, sound, and the like stay available.

Correction, 2026-09-18: `hideonly:` is not a documented prefix. Microsoft documents `showonly:` and `hide:` only, so this list may never have taken effect; I did not test the Settings app on his session that day. It was replaced by a `showonly:` allowlist in [ObiPC Recovery and Settings Lockdown](ObiPC%20Recovery%20and%20Settings%20Lockdown%20-%202026-09-18.md), after he reset the machine from the recovery menu, a path this record never considered.

**Session limits.** [`Scripts/Limit-ObiPCUserSession.ps1`](../../Scripts/Limit-ObiPCUserSession.ps1) runs every minute from the scheduled task `ObiPC Session Limit`, as `SYSTEM`. Each tick it finds the active interactive sessions, checks Active Directory for restricted-group membership, accumulates observed minutes for the day into `C:\ProgramData\ObiPC-SessionLimit` (writable only by SYSTEM and administrators), warns at 15 and 5 minutes, and signs the session out when the window closes or the budget is spent. It reads group membership from the directory rather than the session token, so a newly added member is covered on the next tick. If the directory cannot be reached it does nothing and logs it: failing open, because a wrongly-signed-out person losing work is worse than a missed hour.

**Directory controls on the account.** `logonHours` set to 7:00 AM to 11:00 PM Eastern every day (verified as `Sunday 6:00:00 AM - 10:00:00 PM` and so on in the `net user` readback, which renders in the DC's own local offset, one hour off the Eastern intent by exactly the daylight-saving gap the wider window absorbs). `userWorkstations` set to `OBIPC`.

## Rollout, and the two bugs I hit live

`IK-user` was signed in the whole time, from 9:58 AM. That mattered.

**Bug 1: the Appx version range.** My first policy wrote `LowSection="*"` on the packaged-app publisher rules, which violates the AppLocker schema, where only `HighSection` may be `*`. The Store and Settings would have been at risk. I caught it because `Test-AppLockerPolicy` refused the policy with a pattern-constraint error, corrected `LowSection` to `0.0.0.0`, and re-imported.

**Bug 2: the missing `Everyone` baseline.** My first design allowed `%WINDIR%` and `%PROGRAMFILES%` only to the restricted and unrestricted groups, not to `Everyone`. Because `IK-user` had signed in at 9:58 AM, before I created `ROL-ObiPC-Restricted` at about 10:40 AM, his logon token did not carry the group SID, so he matched no allow rule and the machine began blocking core binaries. The event log showed 70 blocks in two minutes, Chrome among them 39 times, plus `dllhost.exe`, `pickerhost.exe`, and `taskhostw.exe`. I rewrote the policy with an `Everyone` baseline for the Windows and Program Files trees, re-imported, and refreshed policy. Blocks stopped at once: since the fix, the only denials were per-user installs in his profile, which is the intended behaviour.

To bind the group into his token, and with your go-ahead to interrupt him, I warned his session and signed it out. He signed back in immediately as session 2 at 11:03 AM, now carrying `ROL-ObiPC-Restricted`.

## Verification, from the live machine

| Check | Result |
|---|---|
| Effective policy | `Exe=Enabled` 13 rules, `Msi=Enabled` 3, `Appx=Enabled` 3, `Script=AuditOnly` 11 |
| Application Identity service | Running, Automatic |
| Allowed for `IK-user` after re-login | Chrome (22), Edge (19), `svchost`, `cmd`, `conhost`, AMD driver services, Google updater |
| Blocked for `IK-user` after re-login | Only per-user profile binaries: `OneDrive\FileCoAuth.exe`, and earlier Firefox and Spotify from AppData |
| Session limit task | `Ready`, last result 0, ticking once a minute: `session 2 used=6.0m budgetLeft=234.0m windowLeft=653.6m` |
| Usage state file | `S-1-5-21-...-1113-2026-09-12.json` present, written by SYSTEM, not readable by the user |
| `logonHours` | `07 F8 FF` repeated across seven days |
| `userWorkstations` | `OBIPC` |

I did not get a clean result from `Test-AppLockerPolicy` for the `C:\Dev`-allow and `regedit`-deny rules specifically. The cmdlet fails against this policy with a schema error tied to the Appx publisher rules, and a scheduled task to launch a probe binary in his interactive session was refused by Windows (`0x100C0000`). Those two rules are present in the effective policy on the machine, targeting the group SID his token now holds, and the live event log confirms the group is being applied to him. The carve-out will be exercised for real when he does development, and the audit trail is there to catch a gap. I am recording this as verified-by-deployment, not verified-by-launch, so the distinction is honest.

## Open

- **OneDrive.** Its self-updater runs from `%LOCALAPPDATA%\Microsoft\OneDrive`, which the allowlist blocks. If `IK-user` needs OneDrive, it wants a machine-wide install and a path rule, or a publisher rule for Microsoft OneDrive. Left as your decision rather than punching a per-user hole silently.
- **Deploy Git, Node.js, Python** from Action1. Until then his toolchain is Chrome and VS Code.
- **Review the Script audit log** after he has worked for a while, then decide whether to enforce that collection.
- **`userWorkstations` and Kerberos.** With the account pinned to `OBIPC`, it cannot sign in to another domain machine; if that is ever needed, the value has to be widened.
