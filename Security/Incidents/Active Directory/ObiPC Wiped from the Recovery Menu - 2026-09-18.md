# ObiPC Wiped from the Recovery Menu

**Created:** 2026-09-18  
**Last updated:** 2026-09-18

## Incident Metadata

| Field | Value |
|---|---|
| Incident ID | ASU-AD-20260918-001 |
| Detected | 2026-09-18, when I found `ObiPC` sitting at the Windows out-of-box screen; exact minute not retained |
| Mitigated | 2026-09-18 11:11 PM EDT, when the recovery environment was disabled on the machine; the remaining controls landed by 11:14 PM |
| Status | Closed, with follow-ups in the [platform TODO](../../../Platforms/Active%20Directory/Documentation/TODO.md) |
| Severity | SEV-4 |
| Impact type | Availability. One workstation wiped to factory state and out of the domain for about two hours; no credential exposure, no evidence of data leaving the machine |
| Affected service | Active Directory workstation `ObiPC`, Secure Client VLAN 60 |
| Affected asset | `ObiPC`, the physical Windows 11 Pro workstation used by `IK-user` |

## Summary

`IK-user`, the restricted standard user on `ObiPC`, reset the machine to factory state from inside Windows: not through the firmware, which is password-locked with external boot disabled, but through the Windows recovery menu. Everything on the disk went with it, including the domain membership, the AppLocker allowlist, the Settings lockdown, the SSH server, the Action1 agent and the applications. I rebuilt and rejoined the machine that evening, recorded in [ObiPC Rebuild and Rejoin](../../../Platforms/Active%20Directory/Documentation/Change%20Records/ObiPC%20Rebuild%20and%20Rejoin%20-%202026-09-18.md), before I knew how it had happened; that record's original line about "corrupting" the installation is corrected there.

The mechanism needed no privilege, no bypass and no password. On Windows 11, Microsoft documents that "Reset this PC, Remove everything" from the recovery environment requires **no authentication** by default, while "Keep my files" prompts for one ([Security Policy CSP, `RecoveryEnvironmentAuthentication`](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-security); [Windows RE technical reference](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/windows-recovery-environment--windows-re--technical-reference)). The recovery menu is reached from the sign-in screen by holding Shift while clicking Restart, which the machine allowed because its power button was on that screen, or by `shutdown /r /o` from any session, or by interrupting the boot twice. The restriction design from 2026-09-12 treated the recovery environment as out of scope, and it was the whole hole.

## Impact

The machine was unusable from the reset until I finished the rebuild at about 7:10 PM, and its local half had to be rebuilt by hand: bootstrap, offline domain join, SSH Manager host keys, time zone, applications, Remote Desktop scope, `C:\Dev`, the Action1 agent, and the hybrid join. The directory side was untouched, and the `D:` volume came through intact.

No data of mine was on `C:`. Whatever `IK-user` kept outside `C:\Dev` went with the reset, and I hold no backups by standing decision, so nothing is recoverable. No credential was exposed: the machine holds no stored secret beyond its own LAPS-managed local account, whose password rotates and was not retrievable from a wiped disk.

## Affected Assets

- `ObiPC`, `192.168.60.102`, computer object `CN=OBIPC,OU=Standard,OU=Workstations`.
- Indirectly, the five policies that target it and the two role groups, all of which held in the directory and reapplied on rejoin.

## Symptoms

The machine was at the Windows 11 out-of-box experience with no domain, no name, and a Pacific clock. Once rebuilt, `C:\Windows\Logs\PBR\ResetSession.xml` on the new installation recorded the reset that produced it: `Scenario="Reset" WipeData="True" OverwriteSpace="True" PreserveWorkplace="False"`, with `HaveOldOS="True"` and `OldOSRootPath="\Windows.old"`, and `ResetConfig.ini` recording `Scenario=Reset`, `Phase=Offline_End`, `Result=0x00000000`. That is a push-button reset with "Remove everything" and "Clean the drive" chosen.

## Timeline

Times are 12-hour Eastern. Files written by the recovery environment carry a UTC clock, so the 8:22 PM to 9:24 PM file times under `C:\Windows\Panther` and `C:\Windows\Logs\PBR` are 4:22 PM to 5:24 PM Eastern; I give the converted values.

| Time | Event | Source |
|---|---|---|
| 4:19 PM | Reset session started while the previous Windows was still running | `C:\Windows\Logs\PBR\SessionID.xml`, written by the online phase |
| 4:22 PM to 4:37 PM | Recovery environment applied the image; `Failed to detect domain join status` and the rollback-folder writes fall in this window | `setuperr.log`, `Panther`, `$SysReset` |
| 4:28 PM | Restart initiated by `winlogon.exe` on `MINWINPC`, "Operating System: Upgrade (Planned)" | System event 1074, stamped 8:28 PM by the recovery environment's UTC clock |
| 5:30 PM | New installation's recorded install time | `Win32_OperatingSystem.InstallDate` |
| 5:31 PM | Out-of-box experience restart | System event 1074 from `CloudExperienceHostBroker.exe` |
| 5:51 PM | I ran the bootstrap and began the rebuild, believing the installation had been corrupted | [rebuild record](../../../Platforms/Active%20Directory/Documentation/Change%20Records/ObiPC%20Rebuild%20and%20Rejoin%20-%202026-09-18.md) |
| 7:10 PM | Rebuild complete, machine joined, hybrid joined, agents installed | same |
| about 7:45 PM | I learned that `IK-user` had reset the machine from within Windows, and started the lockdown | this record |
| 11:11:57 PM | `reagentc /disable`: *Operation Successful*, recovery environment `Disabled` | `C:\ProgramData\ObiPC-Lockdown\recovery.log` |
| 11:13:24 PM | `RecoveryEnvironmentAuthentication` set to 1 through the local MDM bridge | same |
| 11:14 PM | `C-WKS-ObiPC-Lockdown` and the new AppLocker policy applied on the machine; AppLocker event 8001 at 11:14:42 PM | `gpupdate`, AppLocker EXE and DLL log |

## Findings

1. **The reset needed no credentials.** Microsoft's own table for `Security/RecoveryEnvironmentAuthentication` shows the default `0` as "Keep my files: prompts for authentication; Remove everything: no authentication required". This is the documented Windows 11 default, not a bypass.
2. **The sign-in screen offered the power button.** `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\shutdownwithoutlogon` read `1` on the rebuilt machine at 7:55 PM, the Windows default. Shift+Restart from that screen reaches the recovery menu without signing in.
3. **The recovery environment was enabled**, `reagentc /info` at 7:59 PM: `Windows RE status: Enabled`, `Windows RE Version: 10.0.26100.9444`.
4. **BitLocker was off**, so the recovery environment had the disk in the clear. Even with a TPM-only protector Microsoft lists only TPM+PIN and password protectors as forcing a recovery-key prompt before a "Remove everything" reset ([BitLocker recovery overview](https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/recovery-overview)).
5. **AppLocker could not have helped.** Shift+Restart is a shell action, not a process launch, and `shutdown.exe` sat inside the `%WINDIR%` allow for `Everyone`. Two interrupted boots reach the same menu with no software involved at all.
6. **The Settings lockdown used an undocumented prefix.** The 2026-09-12 policy wrote `SettingsPageVisibility = hideonly:...`; Microsoft documents only `showonly:` and `hide:`. Whether Windows honoured it is unknown, and it was not the path taken, but it means the Recovery page may have been reachable too.
7. **No trace of the previous installation survives.** `Windows.old` is gone (`WipeData="True"`), so which of the three entry points he used cannot be established. Shift+Restart on the sign-in screen is the most likely, because it needs nothing but the mouse.

## Root Cause

A Windows 11 default I had not closed. The 2026-09-12 restriction work controlled what the account could run and see inside Windows, and left the recovery environment, which sits underneath Windows and authenticates nobody for a full wipe, exactly as Microsoft ships it. The two settings that made it reachable without signing in, the sign-in screen power button and the enabled recovery environment, were both defaults.

## Corrective Action

All applied on 2026-09-18 and recorded with readbacks in [ObiPC Recovery and Settings Lockdown](../../../Platforms/Active%20Directory/Documentation/Change%20Records/ObiPC%20Recovery%20and%20Settings%20Lockdown%20-%202026-09-18.md):

- Recovery environment disabled on the machine, and kept disabled by a SYSTEM scheduled task at every boot and daily, because a feature update re-enables it.
- `RecoveryEnvironmentAuthentication` set to require an administrator account for every recovery tool, through the local MDM bridge and through Group Policy on the registry value it redirects to, so a re-enabled recovery environment still refuses a wipe without credentials.
- Sign-in screen power button removed (`shutdownwithoutlogon = 0`); power menu removed from Start and Ctrl+Alt+Del for the restricted group (`NoClose`).
- `shutdown.exe`, the reset entry points, the boot and recovery tools, and the script and DLL hosts denied to the restricted group in AppLocker by path and by publisher, including the copies under `WinSxS`.
- Settings reduced to a `showonly:` allowlist, Control Panel reduced to a named allowlist, MMC snap-ins blocked, App Installer and sideloading closed, Windows Update UI removed, and the rest of the surface listed in the change record.

## Validation

At 11:14 PM: `reagentc /info` reads `Windows RE status: Disabled`; `HKLM\SOFTWARE\Policies\Microsoft\WinRE` holds `WinREAuthenticationRequirement = 1` and `DisableSetup = 1`; `shutdownwithoutlogon = 0`; the effective AppLocker policy carries 56 executable rules of which 44 are denies for the restricted group, and `Test-AppLockerPolicy` against the effective policy returns `Denied` for `shutdown.exe`, `SystemSettingsAdminFlows.exe`, `mshta.exe`, `regsvr32.exe`, `control.exe`, `MSBuild.exe` and both registry editors for the restricted group's SID, and `Denied` for the `WinSxS` copy of `shutdown.exe`.

Not validated: what the Shift+Restart menu shows with the recovery environment disabled, and the behaviour of the user-side policies, because `IK-user` has not signed in since the rebuild. Both are open items in the change record.

## Closure

Closed 2026-09-18. The lesson for the [restriction design](../../../Platforms/Active%20Directory/Documentation/Change%20Records/ObiPC%20Restricted%20User%20Setup%20-%202026-09-12.md) is that a restricted account on a physical machine has to be restricted below Windows as well as inside it, and that BitLocker with a PIN is the control that would have made the recovery environment harmless rather than merely hidden. That is now the recommended baseline, tracked in the platform TODO.
