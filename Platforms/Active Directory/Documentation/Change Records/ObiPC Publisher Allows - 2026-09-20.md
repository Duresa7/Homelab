# ObiPC Publisher Allows

**Created:** 2026-09-20  
**Last updated:** 2026-09-20

Two batches on the same evening, both in `C-WKS-ObiPC-AppControl`, both scoped to `ROL-ObiPC-Restricted`. The first was for App Portal's catalog; the second was for the games and the graphics software he already had and could not run. Seven publisher rules in total, Exe rules 48 to 55.

## First batch: the App Portal catalog

`IK-user` asked for Spotify, Discord, Roblox and VALORANT through App Portal. All four install into the profile of whoever asks for them, and the AppLocker policy I imported on 2026-09-18 gives his group no allow rule of its own: what runs for him is `%WINDIR%` and the two Program Files trees. An installer in a temporary directory and an application in his profile are neither, so all four would have installed into a place he cannot run them from, assuming they installed at all.

I added four publisher allow rules to `C-WKS-ObiPC-AppControl`, one per vendor, scoped to `ROL-ObiPC-Restricted`. Nothing else in the policy changed. The App Portal side of this work is in its own [change record](../../../App%20Portal/Documentation/Change%20Records/Version%200.6.0,%20the%20Agent%20and%20the%20Game%20Catalog%20-%202026-09-20.md).

## Why publisher rules and not paths

A path rule for `%LOCALAPPDATA%\Discord\*` allows a directory he can write to, which is the same shape as the `C:\Dev` carve-out the second pass closed on 2026-09-18: anything he gets into that directory runs. A publisher rule follows the code signature instead, so a program he downloads himself still will not run no matter where he puts it, while the four applications keep working when they update themselves, which all four do from inside the profile.

The rules are deliberately wide within each vendor: `ProductName` and `BinaryName` are both `*`, so anything those four companies sign will run for him. That is the trade I made for four applications that update themselves constantly and rename their binaries between versions.

## The rules

I generated each publisher string with `Get-AppLockerFileInformation` against the vendor's own installer, downloaded on `ObiPC` and checked against the SHA-256 in its `microsoft/winget-pkgs` manifest, rather than writing out what a certificate subject usually looks like.

| Rule Id suffix | Name | PublisherName |
|---|---|---|
| `...140` | Restricted: allow Spotify (publisher) | `O=SPOTIFY AB, L=STOCKHOLM, C=SE` |
| `...141` | Restricted: allow Discord (publisher) | `O=DISCORD INC., L=SAN FRANCISCO, S=CALIFORNIA, C=US` |
| `...142` | Restricted: allow Roblox (publisher) | `O=ROBLOX CORPORATION, L=SAN MATEO, S=CALIFORNIA, C=US` |
| `...143` | Restricted: allow Riot Games (publisher) | `O=RIOT GAMES, INC., L=LOS ANGELES, S=CALIFORNIA, C=US` |

Steam has no rule and needs none: it installs machine-wide into Program Files, which the `Everyone` rules already cover. The Riot rule is there for the day VALORANT is installed by an administrator, since Vanguard needs rights `IK-user` does not have.

The full policy is in [`Configuration/ObiPC-AppLocker.xml`](../../Configuration/ObiPC-AppLocker.xml), updated to match.

## Getting it into the GPO

`Set-AppLockerPolicy -Ldap ... -Merge` has to run somewhere with network credentials, and an SSH session on the controller has none. `Test-Path` against `\\ad.alphasecunited.com\SysVol\...` returns `False` in that session while the same path under `C:\Windows\SYSVOL\` returns `True`, which is the double hop showing itself in a new place.

A SYSTEM scheduled task on `HQ-DC01` did the merge at 7:03 PM. Two details made the difference: the LDAP path needs an explicit server, `LDAP://hq-dc01.ad.alphasecunited.com/CN={...},CN=Policies,CN=System,DC=ad,DC=alphasecunited,DC=com`, and `Set-AppLockerPolicy` is the only half that works. `Get-AppLockerPolicy -Ldap` hung for over ten minutes in both the SYSTEM and the administrator context, with and without the server prefix, and never returned. I abandoned reading the policy back that way and verified on the workstation instead, which is the better check anyway.

The GPO computer version went to 10, with `DSVersion` and `SysvolVersion` matching.

## Verification

`gpupdate /target:computer /force` on `ObiPC` as SYSTEM, then against the effective policy on the machine at 7:05 PM:

| Check | Result |
|---|---|
| Effective policy contains `SPOTIFY AB` | True |
| Exe collection | Enabled, 52 rules, up from 48 |
| Msi collection | Enabled, 4 rules, unchanged |
| Appx collection | Enabled, 7 rules, unchanged |
| Script collection | AuditOnly, 12 rules, unchanged |

`Test-AppLockerPolicy` against the effective policy for the restricted group's SID, on the four downloaded installers:

| File | Decision | Matching rule |
|---|---|---|
| Spotify installer | Allowed | Restricted: allow Spotify (publisher) |
| Discord installer | Allowed | Restricted: allow Discord (publisher) |
| Roblox installer | Allowed | Restricted: allow Roblox (publisher) |
| Riot installer | Allowed | Restricted: allow Riot Games (publisher) |

A copy of `notepad.exe` placed at `C:\Users\Public\probe-denied.exe` returns `DeniedByDefault` for the same SID, so the lockdown still refuses an ordinary executable outside the allowed trees. I removed the probe and the four installers afterwards.

The real proof came from the portal an hour later. Spotify, Roblox and Discord all installed into his profile and are present on disk, each having run an installer from a temporary directory that would have been denied that morning.

## What did not change

The packaged-app denies stay exactly as they were: App Installer, the Microsoft Store, the Store purchase app and the Xbox app are all still denied to his group. Keeping winget shut is why App Portal installs these four through direct installers rather than through winget. The Msi collection still carries its `Deny *` for him, and he still has no allow rule of his own for anything outside `%WINDIR%` and Program Files beyond these four signatures.


## Second batch: his games

He could not launch Rainbow Six Siege, and reported BattlEye as the thing being blocked. BattlEye was not being blocked. Its executables live in `C:\Program Files (x86)\Common Files\BattlEye\`, which the `Everyone` Program Files rule already allows, and six hours of AppLocker denials contained no BattlEye entry at all. Over that window exactly two binaries were denied, and both were in his profile:

- `%LOCALAPPDATA%\Ubisoft\R6S\RainbowSix.exe`, twice at 7:47 PM
- `%LOCALAPPDATA%\NVIDIA Corporation\NVIDIA app\NvBackend\ApplicationOntology\OAWrapper.exe`, four times

BattlEye launches the game, the game executable was denied, and BattlEye reported the failure. That is why it looked like the anti-cheat.

Three more rules, publisher strings again taken from the files themselves with `Get-AppLockerFileInformation`:

| Rule Id suffix | Name | PublisherName |
|---|---|---|
| `...144` | Restricted: allow Ubisoft (publisher) | `O=UBISOFT ENTERTAINMENT INC., L=SAN FRANCISCO, S=CALIFORNIA, C=US` |
| `...145` | Restricted: allow NVIDIA (publisher) | `O=NVIDIA CORPORATION, L=SANTA CLARA, S=CALIFORNIA, C=US` |
| `...146` | Restricted: allow BattlEye (publisher) | `O=BATTLEYE INNOVATIONS E.K., L=REUTLINGEN, S=BADEN-WÜRTTEMBERG, C=DE` |

The BattlEye rule fixes nothing today and is there on purpose: other titles ship their BattlEye components inside the game directory rather than in Common Files, and those would land in the profile where the same denial applies. Note the umlaut in the publisher string; it has to match the certificate exactly, so the policy file is UTF-8 and stays that way.

Merged at 7:56 PM by the same SYSTEM scheduled task with the explicit server in the LDAP path. GPO computer version went to 11.

### Verification of the second batch

After `gpupdate /target:computer /force` on `ObiPC`, the effective policy read Exe Enabled **55**, with Msi 4, Appx 7 and Script AuditOnly 12 all unchanged. `Test-AppLockerPolicy` for the restricted group's SID:

| File | Decision | Matching rule |
|---|---|---|
| `RainbowSix.exe` in his profile | Allowed | Restricted: allow Ubisoft (publisher) |
| `OAWrapper.exe` in his profile | Allowed | Restricted: allow NVIDIA (publisher) |
| `BEService.exe` | Allowed | Restricted: allow BattlEye (publisher) |
| `BEService_r6s.exe` | Allowed | Restricted: allow BattlEye (publisher) |

A fresh copy of `notepad.exe` at `C:\Users\Public\probe2.exe` returned `DeniedByDefault` for the same SID, and was removed afterwards. The packaged-app denies on App Installer, the Microsoft Store, the Store purchase app and the Xbox app are untouched, so nothing here gives him a new way to install software: these rules govern what may run, not what may be installed.

What he gains beyond the two blocked binaries: anything signed by Ubisoft, NVIDIA or BattlEye now runs for him from anywhere, including a Ubisoft title he installs later. That is the trade a publisher rule makes, and it is the narrower of the options, because the alternative that covers a self-updating game is a path rule over a directory he can write to.
