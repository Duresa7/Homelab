# ObiPC Event Review

**Created:** 2026-09-23  
**Last updated:** 2026-09-23

I reviewed ObiPC's local Windows events from midnight through approximately 11:34 PM EDT on 2026-09-23. I queried Security, System, Application, Windows Defender Operational, and all four AppLocker channels through SSH Manager. This was a read-only review after the [account disablement and sign-in check](../../Platforms/Active%20Directory/Documentation/Change%20Records/IK-user%20Account%20Disabled%20-%202026-09-23.md). I found operational errors and application-control blocks, but these checks did not establish another security incident.

## Observed events

| Time (EDT) | Finding | Verification and limits |
|---|---|---|
| 12:33:52 PM | `AppPortal.Agent.exe` 0.6.0.0 crashed, Application Error 1000 and .NET Runtime 1026 | Exception code `e0434352`; `System.OperationCanceledException` in the Windows service shutdown path. MSI events 1033 and 11707 recorded App Portal 0.8.0 installation at 12:34:01 PM. The sequence is consistent with an upgrade-related shutdown failure, but I did not establish causality. At review time, `AppPortalAgent` was running and the binary version was 0.8.0.0. |
| 12:34:00 PM to 11:29:22 PM | 134 App Portal warnings in the initial sample | 132 warning messages contained the numeric value `404`; two contained `TaskCanceledException`. A later sample showed `ManagerReporter` and `JobRunner` categories. I did not retain full messages or verify the affected endpoint or whether installation/reporting was impaired. Counts are point-in-time because warnings continued during review. |
| 12:51:04 AM, 2:42:03 AM, 4:33:04 AM, 11:03:04 PM | Four Group Policy 1030 authentication errors | Each returned error 1326, `The user name or password is incorrect.` The first three named `HQ-DC02`; the last named `HQ-DC01`. Three precede account disablement. I did not attribute the events to a particular user or test which policy refreshes failed. |
| 8:09:27 AM to 9:29:07 PM | Ten AppLocker executable blocks, event 8004 | Four `FILECOAUTH.EXE`, two `ONEDRIVESTANDALONEUPDATER.EXE`, and four `NGENTASK.EXE`. The filenames identify blocked executables, not deliberate actions by a person. Four DistributedCOM 10000 errors appeared from 8:09:27 AM to 8:24:30 AM, overlapping the FileCoAuth blocks; I did not establish their cause. |
| 9:28:19 PM to 11:07:06 PM | Four packaged-app deployment blocks and corresponding Windows Update failures | AppLocker 8025 and WindowsUpdateClient 20: Gaming App at 9:28:19 PM, Store Purchase App at 9:28:28 PM, Desktop App Installer at 11:06:56 PM and 11:07:06 PM. Each update error was `0x80073d01`, which Microsoft defines as [deployment blocked by policy](https://learn.microsoft.com/en-us/windows/win32/appxpkg/troubleshooting). These packages are already named in the workstation's documented restrictions. |
| 12:00:28 AM to 11:07:45 PM | Twenty Bluetooth USB driver errors, BTHUSB 5 | Message: `The Bluetooth driver expected an HCI event with a certain size but did not receive it.` I did not test Bluetooth hardware or connectivity. |

Microsoft's [AppLocker event reference](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/applocker/using-event-viewer-with-applocker) identifies 8004 as an enforced executable block. The MSI/Script and packaged-app execution queries returned no warning/error matches in their selected categories.

## Security and continuity checks

The selected Security events returned only the two previously recorded failed interactive logons at 9:26:29 PM and 9:26:33 PM. At 11:34:31 PM, the query for audit-policy changes, Security-log clearing, selected account/group changes, service installation, and scheduled-task creation/update returned zero events. This is a result for the queried IDs, not proof that every possible action was audited.

The Defender query returned no threat-detection or remediation events and no selected protection-disable events. It returned two configuration events, 5007, at 10:09:59 AM and 11:06:37 PM; both changed only the recorded `CoreService\WdConfigHash` value. Antivirus, antispyware, real-time protection, behavior monitoring, and network inspection were all enabled at review time. I did not run a new antivirus scan.

The System query found no events among 41, 1074, 6005, 6006, 6008, 104, and 7045 today. The operating system reported its last boot as 2026-09-21 at 8:08:05 AM EDT. I found no restart or unexpected-shutdown evidence in those checks.

## Remaining work and evidence

I did not change policy, repair services, terminate sessions, or restart the workstation. App Portal reporting warnings, the Group Policy failures, and the Bluetooth errors remain unexplained by this review. The App Portal service running does not prove its end-to-end functions work. I did not infer malicious intent from routine application blocks or claim that the absence of selected log events proves the absence of compromise.

No separate raw terminal capture was retained for these checks. The table records the selected event fields and current-state readbacks; names, directory identifiers, and user-profile paths were excluded before results were returned. No snapshots or backups were created.
