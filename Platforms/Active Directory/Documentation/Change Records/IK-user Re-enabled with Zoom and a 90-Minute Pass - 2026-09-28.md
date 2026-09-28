# IK-user Re-enabled with Zoom and a 90-Minute Pass

**Created:** 2026-09-28  
**Last updated:** 2026-09-28

On 2026-09-28 I brought `IK-user` back on `ObiPC` for about an hour, with conditions. The account had been disabled since the [2026-09-23 disablement](IK-user%20Account%20Disabled%20-%202026-09-23.md). I installed Zoom for all users, and Logi Options+ once he asked for it. I also put back the session-limit task as a one-time pass of 90 minutes of signed-in time. When the pass was spent, the task was to sign him out and have ObiPC refuse his sign-in until I reset it. I did the work in the order that kept him locked out until the limit was running: Zoom first, then the limit, then the account.

The account was enabled from 4:19 PM. `IK-user` signed in at 4:21 PM. The first two ticks after that missed him because of a bug that goes back to 2026-09-18, described below, and the pass counted his time from 4:24:20 PM. At 5:16 PM I disabled the account again and removed the pass with 52 of its 90 minutes used. Zoom and Logi Options+ stay installed.

## Zoom

I installed Zoom's IT-admin MSI over SSH as `local-obipc` rather than through Action1. That MSI installs per machine into `C:\Program Files\Zoom\bin`, which the `Everyone: Program Files` AppLocker rule already covers. Zoom's other download is a per-user installer that installs into `%APPDATA%\Zoom\bin`, and that path is blocked for him.

| Step | Result |
|---|---|
| Download | `https://zoom.us/client/latest/ZoomInstallerFull.msi?archType=x64` with `curl.exe`, exit 0, 220,297,216 bytes |
| Signature | `Valid`, `CN="Zoom Communications, Inc."` |
| SHA-256 | `B0DAC9FA5237D2E18144CA723644460E7CC26675E5D3DB0F89FDFE47AD8C429B` |
| Install | `msiexec /i ... /qn /norestart DISABLEADVTSHORTCUTS=1`, exit 0; log line *Installation completed successfully* at 4:15:56 PM |
| Product | `Zoom Workplace (64-bit)` 7.2.48556, `ALLUSERS = 1` |
| Service | `ZoomCptService`, Running, Automatic |
| Shortcuts | Start menu and Public desktop `Zoom Workplace.lnk`, both targeting `C:\Program Files\Zoom\bin\Zoom.exe` directly |
| Join links | `zoommtg` registered machine-wide to `"C:\Program Files\Zoom\bin\Zoom.exe" "--url=%1"`, so a join link in Chrome opens the app |
| WebView2 runtime | 153.0.4234.48 present |
| Cleanup | `C:\Windows\Temp\ZoomDeploy`, holding the MSI and install log, removed; readback `False` for `Test-Path` |

I used `DISABLEADVTSHORTCUTS=1` as a precaution. An advertised shortcut can start a Windows Installer repair when a new user launches it for the first time. The MSI collection carries `Deny *` for `ROL-ObiPC-Restricted`, so that repair would be refused and the launch could fail. With the property set, both shortcuts point straight at the executable, as the table shows.

AppLocker against the effective policy, for `Zoom.exe`, `CptHost.exe` (screen sharing), `aomhost64.exe`, `zWebview2Agent.exe` and `Zoom_launcher.exe`:

| Principal tested | Decision |
|---|---|
| `ROL-ObiPC-Restricted` SID | `DeniedByDefault` for all five, meaning no rule names the group for these files and no deny applies |
| `Everyone` (`S-1-1-0`) | `Allowed` for all five, matching rule `Everyone: Program Files` |

As the [2026-09-18 record](ObiPC%20Recovery%20and%20Settings%20Lockdown%20-%202026-09-18.md) notes, `Test-AppLockerPolicy -User` matches only rules that name that SID. Taken together, the two results mean he can run all five. All five files are validly signed by Zoom Communications, Inc. Camera and microphone consent are `Allow` at `HKLM\...\CapabilityAccessManager\ConsentStore`, and no `AppPrivacy` policy is set. The Privacy pages are outside his `showonly:` Settings list, so he cannot turn either off himself.

## Logi Options+

He asked for Logi Options+ at about 4:25 PM, while he was signed in. ObiPC has a Logitech USB LIGHTSPEED receiver and an MX Brio camera attached. I ran the install from a one-off `SYSTEM` task so it would outlive the SSH call. Logitech's installer puts the application under `C:\Program Files`, which the `Everyone` rule covers. Nothing was allowed for this install and no AppLocker rule changed.

| Step | Result |
|---|---|
| Download | `https://download01.logi.com/web/ftp/pub/techsupport/optionsplus/logioptionsplus_installer.exe`, `curl.exe` exit 0, 49,871,512 bytes, at 4:26:13 PM |
| Signature | `Valid`, `CN=Logitech Inc, O=Logitech Inc, L=Newark, S=California, C=US`; the task was written to stop on anything else |
| SHA-256 | `3ED465B68280A68C8F1FA8B1769C06325052237946C9E1915F8E2B3EBE2F5FE9` |
| Install | `/quiet /analytics No`, exit 0 at 4:26:47 PM |
| Products | `Logi Options+` 2.7.961922, `Logi Plugin Service` 6.4.1.3246, `Logi RightSightForWebcams` 1.2.272.0 |
| Services | `OptionsPlusUpdaterService` and `logi_lamparray_service`, both Running, Automatic |
| In his session | `logioptionsplus.exe` (5 processes), `logioptionsplus_agent.exe` and `logioptionsplus_appbroker.exe` running in session 1 from `C:\Program Files\LogiOptionsPlus`; the updater runs as `SYSTEM` |
| AppLocker | All 7 executables under `C:\Program Files\LogiOptionsPlus`: `Allowed` for `Everyone`, no explicit deny for the restricted group; no EXE 8004 from 4:26 PM to 4:27:42 PM |
| Cleanup | Deploy task unregistered, `C:\Windows\Temp\LogiDeploy` and the task script removed; all three read back absent |

The installer also staged executables under `C:\ProgramData\LogiOptionsPlus` (16, of which 5 are in `depots\853130\logioptionsplus`) and `C:\ProgramData\Logishrd` (11). No rule allows that tree for him, so any of them launched in his session would be blocked. The updater service that uses them runs as `SYSTEM`, which AppLocker does not evaluate. Whether self-updates complete has not been tested.

## The 90-minute pass

[`Scripts/Limit-ObiPCUserSession.ps1`](../../Scripts/Limit-ObiPCUserSession.ps1) was retired on 2026-09-18 with a daily 240-minute budget and an 8 AM to 10 PM window. I rewrote it for this request:

- **One pass, not a daily budget.** Each member of `ROL-ObiPC-Restricted` gets 90 minutes of Active signed-in time, stored in `C:\ProgramData\ObiPC-SessionLimit\<SID>-pass.json`. Signing out keeps what is left. Nothing resets it at midnight. The window logic is gone, and `logonHours` of 7 AM to 11 PM on the account remain the time-of-day control.
- **Warnings** at 15, 5 and 1 minute left, through `msg.exe`.
- **The lockout.** When the pass reaches zero, the script adds the SID to `SeDenyInteractiveLogonRight` and `SeDenyRemoteInteractiveLogonRight` in ObiPC's local security database and then signs out every session the account has. The deny goes first, so there is no gap in which to sign straight back in. It uses `LsaAddAccountRights` and `LsaRemoveAccountRights`, which change one SID's rights and leave every other entry alone.
- **The reset** is `Limit-ObiPCUserSession.ps1 -Reset -Account <sAMAccountName>`, run as an administrator on ObiPC. It removes both rights and deletes the pass file, so the next sign-in starts a fresh 90 minutes.
- **Directory outage.** Before, the script failed open whenever Active Directory was unreachable. Now an account that already has a pass file stays restricted, so pulling the network cable after sign-in does not stop the clock. An account with no pass file is still left alone.
- **Two sessions for one account** spend the pass once per tick, not twice.

No Group Policy object in the domain defines user rights for ObiPC. I read every GPO report on `HQ-DC01`, and only `Default Domain Controllers Policy` carries `UserRightsAssignment`. A policy refresh therefore does not overwrite the local deny. Before the change, ObiPC's `SeDenyInteractiveLogonRight` was `Guest` alone.

### Deployment

| Item | Value |
|---|---|
| Script | `C:\Program Files\ObiPC-SessionLimit\Limit-ObiPCUserSession.ps1`, SHA-256 `6a8f9aa6c59babd970a2f9c2e967451323fc800c07f2232528f087516b54974e` after the fix below, matching this repository; `1f39152d912e635a3df9a988f33294b4b470996e9216d606d410bf507d5c4ec4` before it |
| Script folder ACL | `TrustedInstaller`, `SYSTEM` and `Administrators` are the only principals with write access |
| State folder | `C:\ProgramData\ObiPC-SessionLimit`, inheritance removed, `SYSTEM` and `Administrators` Full Control only; `icacls` exit 0 |
| Task | `ObiPC Session Limit`, `SYSTEM`, highest run level, one-minute repetition with no end, five-minute execution limit, ignore new instance, start when available, runs on battery |
| First ticks | 4:19:19 PM and 4:20:20 PM, last result 0, no missed runs, nobody signed in |

### Mechanism test on testuser

A signed-in session is the only full test, and I had none to use. I tested the lock and reset against `testuser`'s SID instead, since `testuser` is also in the restricted group:

| Step | Readback |
|---|---|
| Add both deny rights | `LsaEnumerateAccountRights` returned `SeDenyInteractiveLogonRight,SeDenyRemoteInteractiveLogonRight` |
| `secedit /export` while denied | `SeDenyInteractiveLogonRight = *<testuser SID>,Guest` and `SeDenyRemoteInteractiveLogonRight = *<testuser SID>` |
| `-Reset -Account testuser` | Rights empty, no pass file |
| `secedit /export` after reset | `SeDenyInteractiveLogonRight = Guest`, no remote-interactive deny line |

So `Guest` survived both directions, and the reset leaves the machine as it was.

### The bug his first sign-in exposed

`IK-user` signed in at the console at 4:21 PM, session 1, `Active`. The 4:22:20 PM tick returned 0 but wrote no log line and no pass file, so it never saw him.

I ran the same steps as `SYSTEM` from a one-off task and wrote the results to a file. `USERDOMAIN` was `ALPHASEC`, the SID resolved to the one ending `-1113`, and the directory lookup found him in `ROL-ObiPC-Restricted`. The session list was the problem. `query.exe user` printed his session and **exited 1**. The idle-machine fix of [2026-09-18](ObiPC%20Rebuild%20and%20Rejoin%20-%202026-09-18.md) treats any non-zero exit as nobody signed in, so from that day on the script could never see a session when run as `SYSTEM`. The fix was only ever tested on an idle machine. On 2026-09-12 the script had no exit-code check and worked with him signed in the whole time.

I removed the exit-code check and now decide from the output alone: fewer than two lines means no sessions. I edited the deployed file in place, read back the new SHA-256 above, and removed the diagnostic task and its files. The next tick counted him:

| Time | Log line |
|---|---|
| 4:24:20 PM | `<SID ...-1113> sessions=1 used=0.0m left=90.0m` |
| 4:25:20 PM | `<SID ...-1113> sessions=1 used=1.0m left=89.0m` |

The pass file read `{"Minutes":0,"LastTick":"2026-09-28T16:24:20...","Warned":[],"LockedAt":null}` after the first of those ticks, and the ticks counted one minute each until I removed the task.

## The account

At 4:19:13 PM on `HQ-DC01` I ran `Enable-ADAccount` against the one member of `ROL-ObiPC-Restricted` that is not `testuser`, which is the same identity match the disablement used. It exited without error.

| Controller | Time | Readback |
|---|---|---|
| `HQ-DC01` | 4:19:13 PM | `Enabled=True`, `LockedOut=False`, `userWorkstations=OBIPC` |
| `HQ-DC02` | 4:19:39 PM | `Enabled=True`, `LockedOut=False`, `userWorkstations=OBIPC` |

My first `HQ-DC02` query ran from `HQ-DC01` with `-Server HQ-DC02` and failed with *Unable to contact the server*, an Active Directory Web Services error. I reran it on `HQ-DC02` against `localhost`, and that is the row above. I did not investigate the cross-controller ADWS failure.

I changed nothing else on the account. His password is still the one he set himself at 9:58:49 AM on 2026-09-12, and it reads `PasswordExpired=False`. His groups, `logonHours` and `userWorkstations` are unchanged. Cloud Sync carries the enabled state to his Microsoft 365 account, so tenant sign-in comes back with it. I did not verify when that sync landed. The ObiPC lockout does not reach the tenant.

## Scope

While it ran, the pass applied to every member of `ROL-ObiPC-Restricted`. That included `testuser`, the 2026-09-19 test fixture, which did not sign in during the hour.

## Disabled again and the pass removed

At 5:16:06 PM on `HQ-DC01` I ran `Disable-ADAccount` against the same identity match. The readback before the change was `Enabled=True`. Both controllers then read the account disabled:

| Controller | Time | Readback |
|---|---|---|
| `HQ-DC01` | 5:16:06 PM | `Enabled=False`, `userWorkstations=OBIPC` |
| `HQ-DC02` | 5:16:27 PM | `Enabled=False`, `userWorkstations=OBIPC`, queried on `HQ-DC02` itself |

Then on ObiPC:

- I unregistered `ObiPC Session Limit`. It read back absent, and `ObiPC Recovery Lockdown` is the only `ObiPC` task left.
- `secedit /export` read `SeDenyInteractiveLogonRight = Guest` and no remote-interactive deny line. The pass was never spent, so no deny had been written.
- His pass file read 52.0 minutes, last tick 5:16:20 PM, `LockedAt` null. I deleted `C:\Program Files\ObiPC-SessionLimit` and `C:\ProgramData\ObiPC-SessionLimit`, and both read back absent.

His console session from 4:21 PM was still open at 5:16:05 PM. As the 2026-09-23 record notes, disabling an account does not end a session that is already running, and I did not sign him out. The script stays in this repository as the versioned reference, with the session-detection fix.

## Something I noticed on the network

At 4:06:37 PM, UniFi recorded a new wired client named `ObiPC` on `192.168.60.219`, on gateway port 6, with a Wistron OUI. On ObiPC that address belonged to `Ethernet 2`, a Realtek USB GbE adapter that Windows first installed at 8:27:17 PM on 2026-09-18. At about 4:12 PM `Ethernet 2` and the Wi-Fi adapter were both `Disconnected`, and ObiPC was answering on its built-in 2.5 GbE port at `192.168.60.102`. The Wi-Fi adapter is recorded on `192.168.10.220`, last seen at 4:07:17 PM. Someone was plugging adapters into the machine shortly before this change. I recorded it and did not investigate further.

## Not verified

- **The warnings, the sign-out and the refused sign-in.** None of them ran, because I removed the pass before it was spent. The mechanism test above covers the rights. It does not cover `msg.exe` delivery, `logoff.exe` on his session, or what the sign-in screen shows once he is denied.
- **Zoom beyond launch.** At 4:24:56 PM two `Zoom.exe` processes were running in his session 1 from `C:\Program Files\Zoom\bin`. Between 4:21 PM and 4:25:17 PM the AppLocker EXE log held two 8004 blocks, and neither was Zoom: OneDrive's `FileCoAuth.exe` in his profile, the known open item, and `DefenderSessionHelper.exe` under `C:\ProgramData\Microsoft\Windows Defender\Platform\4.18.26080.4-0`. The MSI and Script log held no 8007. I have not observed audio, camera, screen sharing or a join link.
- **Action1 patching of Zoom and Logi Options+.** I installed neither through Action1, so I have not confirmed the console lists or patches them.
- **Logi Options+ with his devices.** I did not see whether it detected the receiver's devices or the MX Brio, or whether a Logitech self-update completes under AppLocker.

No snapshots or backups were created. No separate terminal capture was retained.
