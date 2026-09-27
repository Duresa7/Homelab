# ObiPC Physical Access Simulation

**Created:** 2026-09-27  
**Last updated:** 2026-09-27

## Incident Metadata

| Field | Value |
|---|---|
| Record ID | ASU-AD-20260927-001 |
| Classification | Authorized physical-access sign-in simulation; incident-response exercise |
| Disposition | Closed as an authorized exercise; follow-up validation remains open |
| Severity | Informational; no confirmed unauthorized access in the reviewed sign-in records |
| Review window | 2026-09-24 8:11:43 AM through 2026-09-27 8:11:43 AM EDT, a fixed 72 hours |
| First and last matching failed attempts | 2026-09-24 3:09:18 PM and 2026-09-27 6:19:38 AM EDT |
| Investigation and evidence collection | 2026-09-27; retained event query completed at 8:21:07 AM, state readback at 8:21:29 AM EDT |
| Authorization and attribution | I confirmed that I was testing what attempted sign-in would look like after someone gained physical access. This is my account of the exercise, not attribution established by Windows logs |
| Affected asset | Physical Windows 11 workstation `OBIPC`, `192.168.60.102`, Secure Client VLAN 60, domain `ad.alphasecunited.com` |
| Account aliases in failed attempts | `IK-user` and `DK-user`; an entered account name does not establish who used the keyboard |
| Detection method | Requested retrospective review of local event logs; no automated alert delivery was validated |
| Evidence | [Collection method, artifacts and integrity hashes](Evidence/ObiPC%20Physical%20Access%20Simulation%20-%202026-09-27/Evidence-Index.md) |

## Summary

I tested attempted sign-in with physical access to ObiPC, then reviewed its Windows logs to determine whether any attempt produced a successful session. I initially requested an undocumented check and subsequently requested this incident-format exercise report and supporting evidence.

In the fixed review window I found **22 failed interactive logon events and no successful human interactive, cached-interactive, unlock or RDP logon events** in the queried Security records. Twenty failures used names mapped to `IK-user`; two used names mapped to `DK-user`. Fifteen failures explicitly reported a disabled account, four reported no available logon servers, and three reported an account-name lookup failure.

The 1,416 successful-logon events were system, virtual-account, computer-account, management-service or investigation activity. I did not count them as successful desktop access. The evidence supports a failed sign-in exercise within this window. It does not establish that every physical-access attack would fail.

## Scope and Impact

I reviewed ObiPC's local Security log and Terminal Services session records. I checked the effective logon audit settings, the retained log boundaries, the reported console user and last boot. I used a directory lookup on `HQ-DC01` during the initial review to resolve the otherwise unidentified network account to `svc-action1-deploy`. I did not perform a new controller-wide authentication search for this report.

I found no successful human session in the selected records and no demonstrated confidentiality, integrity or availability impact from a successful sign-in. I did not examine file access, disk contents, memory, persistence, removable media, firmware changes or network exfiltration. Those impacts therefore remain outside the assessment rather than independently disproved.

I made no containment, account, password, audit-policy, firewall or endpoint configuration changes during the investigation. Read-only remote collection still creates authentication and process activity on the endpoint; the first such authentication falls inside the selected window.

The earlier [recovery-menu wipe](ObiPC%20Wiped%20from%20the%20Recovery%20Menu%20-%202026-09-18.md) is a separate incident. I did not repeat or validate a recovery-menu or offline-disk attack in this exercise.

## Symptoms and Detection

I began with a request to determine whether anyone had successfully signed in during the preceding three days. ObiPC answered SSH at 8:11:42 AM EDT on 2026-09-27, allowing a direct read of its local logs. This resolves the local-log access limitation of the [2026-09-24 sign-in review](../../Assessments/ObiPC%20Sign-In%20Review%20-%202026-09-24.md) for this collection; it does not change what was reachable on that earlier date.

Every failed event in the retained export is Security event 4625, logon type 2, with source address `127.0.0.1`, domain `ALPHASEC`, and caller `C:\Windows\System32\svchost.exe`. I interpret these as local interactive authentication failures. Local event fields support that interpretation, while my statement supplies the physical-access exercise context. They cannot distinguish a particular person at the keyboard or reconstruct each action I took.

## Timeline

All times below are EDT. Record IDs refer to ObiPC's Security log. The export preserves source UTC timestamps and subsecond precision.

| Date and time | Observation | Evidence |
|---|---|---|
| 2026-09-23 8:24:48 PM | I previously disabled `IK-user`; this predates the exercise review window | [Account disablement record](../../../Platforms/Active%20Directory/Documentation/Change%20Records/IK-user%20Account%20Disabled%20-%202026-09-23.md) |
| 2026-09-24 8:11:43 AM | Fixed review window begins | Event query bounds |
| 2026-09-24 3:09:18 PM | One `IK-user` failure reported a disabled account | 22608 |
| 2026-09-24 9:59:59 PM to 10:11:53 PM | Four `IK-user` failures reported no available logon servers | 22998, 23034, 23052, 23053 |
| 2026-09-26 12:30:06 AM to 12:30:09 AM | Four `IK-user` failures reported a disabled account | 23485–23488 |
| 2026-09-26 7:51:55 PM to 7:52:08 PM | Two `IK-user` failures reported a disabled account | 25168–25169 |
| 2026-09-26 11:42:07 PM | Last boot reported by Windows at collection | State readback; reason for restart not investigated |
| 2026-09-26 11:42:56 PM to 11:42:58 PM | Two `IK-user` failures reported a disabled account | 25321–25322 |
| 2026-09-26 11:43:07 PM and 11:43:13 PM | Two failures using names mapped to `DK-user` reported an account-name lookup failure | 25325–25326 |
| 2026-09-26 11:43:21 PM | One failure using a name mapped to `IK-user` reported an account-name lookup failure | 25329 |
| 2026-09-26 11:52:17 PM | One `IK-user` failure reported a disabled account | 25357 |
| 2026-09-27 12:48:22 AM to 12:48:23 AM | Three `IK-user` failures reported a disabled account | 25424–25426 |
| 2026-09-27 1:11:08 AM and 6:19:38 AM | Two further `IK-user` failures reported a disabled account | 25465, 25811 |
| 2026-09-27 8:11:42 AM | My initial SSH check generated two `local-obipc` type-3 logon events and an SSH service-account type-5 event | Successful-logon summary; initial investigation |
| 2026-09-27 8:11:43 AM | Fixed review window ends | Later collection activity is outside the event query |
| 2026-09-27, before 8:21:07 AM | Two attempts to run a combined evidence query were rejected with `The command line is too long.`; I split the query | Collection failure export; exact attempt times not retained |
| 2026-09-27 8:21:07 AM | I repeated the event query for the same fixed window: 1,416 successes, 22 failures, zero human interactive successes | Event review export, exit code 0 |
| 2026-09-27 8:21:29 AM | I verified retained log coverage and effective auditing; no console user was reported | State readback export, exit code 0 |

## Findings

### Failed sign-ins

| Entered identity alias | Count | Status / substatus | Interpretation |
|---|---:|---|---|
| `IK-user` | 15 | `0xc000006e / 0xc0000072` | Account restriction; disabled account |
| `IK-user` | 4 | `0xc000005e / 0x0` | No logon servers available |
| `IK-user` | 1 | `0xc000006d / 0xc0000064` | Logon failure; specified account name not found |
| `DK-user` | 2 | `0xc000006d / 0xc0000064` | Logon failure; specified account name not found |
| **Total** | **22** | | **All logon type 2** |

I used Microsoft's [4625 field documentation](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4625) and [NTSTATUS definitions](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55) to interpret the event fields and codes. The three lookup failures do not prove the intended directory accounts were missing or disabled. I did not preserve the entered spelling as a public identity or investigate its exact mismatch. I did not capture or independently validate the passwords supplied.

### Successful authentication without a human desktop session

| Account or category | Logon type | Count | Assessment |
|---|---:|---:|---|
| `SYSTEM` | 5 | 1,253 | Service activity |
| `SYSTEM` | 0 | 6 | System activity |
| `LOCAL SERVICE`, `NETWORK SERVICE` | 5 | 12 | Six events for each service identity |
| SSH service account | 5 | 1 | Initial investigation connection |
| `OBIPC$` | 3 | 50 | Computer-account network authentication |
| `svc-action1-deploy` | 3 | 68 | Network authentication under the deployment account; individual management operations not reconstructed |
| `local-obipc` | 3 | 2 | My initial SSH check, recorded through `sshd` |
| `DWM-1`, `UMFD-0`, `UMFD-1` | 2 | 24 | Windows virtual-account sessions, excluded from human sign-in results |
| **Total** | | **1,416** | **Zero successful human interactive events in the query** |

I distinguished interactive, network and service logons using Microsoft's [4624 logon-type documentation](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4624). Counting every 4624 event as a person signing in would have produced the wrong result.

### Audit coverage and confidence

I found the oldest retained Security event at 2026-09-18 5:37:25 PM EDT, before the review window, and the newest at 2026-09-27 8:19:03 AM EDT in the state readback. `Logon` auditing reported `Success and Failure`. The query found no Security events 1102 or 4719 in the window. These observations support log coverage; they are not a forensic guarantee against tampering or every possible collection gap.

I found no matching human 4624 events of types 2, 7, 10, 11, 12 or 13, and no Terminal Services LocalSessionManager events 21 or 25 in the window. The repeated query matched the initial counts. Confidence is high in those bounded query results.

`Other Logon/Logoff Events` reported `No Auditing`. The absence of 4778 and 4801 events therefore does not independently prove that no reconnect or unlock occurred. `Win32_ComputerSystem.UserName` returned null, which means no console user was reported at collection; I did not enumerate every possible disconnected session.

## Cause and Interpretation

I caused the attempted access as an authorized physical-access simulation. The observed rejection reasons were account disablement, unavailable logon servers and unsuccessful account-name resolution. I found no successful authentication bypass in the selected records.

The 15 disabled-account failures are consistent with the account disablement recorded on 2026-09-23. I did not revalidate the account's current state on both controllers for this report. The four no-logon-server failures do not by themselves prove that I unplugged the network or that a particular online-only policy caused the rejection. I did not capture a step-by-step exercise plan, network-disconnection timestamps or the passwords supplied.

The logs establish attempted identities and outcomes, not the identity of the person making each attempt. My confirmation establishes the exercise context. I have no independently recorded mapping from each physical action to each event.

## Response and Corrective Action

I completed the response as a read-only investigation: I defined the window, queried the workstation, separated human attempts from system and management logons, verified auditing and retention, and repeated the query while retaining sanitized evidence. I did not isolate or rebuild the workstation, rotate credentials, enable accounts, or alter policy because I found no confirmed unauthorized access and identified the activity as my exercise.

I retained selected-field JSON exports, the exact queries, command exit status and stderr, a record of the rejected combined query, and an integrity manifest. I did not acquire an EVTX image, memory image or disk image. The exported evidence supports this review and is not a forensic acquisition of the machine.

I placed the remaining work in the [Active Directory follow-up list](../../../Platforms/Active%20Directory/Documentation/TODO.md#physical-access-exercise-follow-ups-2026-09-27). It covers separate unlock/reconnect auditing, validation of centralized detection, and a controlled retest with recorded inputs and expected outcomes. Existing offline sign-in and BitLocker work remains open. No hardening change is claimed by this report.

## Validation and Closure

I reconciled the successful-event categories to 1,416, verified that the 22 failed events have 22 distinct record IDs, and checked the failure breakdown of 20 `IK-user` and two `DK-user` events. Both retained readbacks exited with code 0 and empty stderr.

I close ASU-AD-20260927-001 as an authorized exercise with no successful human sign-in found in the fixed review window. This closure does not certify resistance to recovery-menu abuse, external boot, offline disk access, local-account attacks, credential theft or an already-open session. Those paths were not assessed.

I will reopen the investigation if additional evidence shows an unexpected human session, activity I cannot account for as part of the exercise, or log coverage that changes these conclusions. The follow-up list has completion criteria; it is not closed by the absence of a successful sign-in.
