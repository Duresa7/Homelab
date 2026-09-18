# ObiPC Rebuild and Rejoin

**Created:** 2026-09-18  
**Last updated:** 2026-09-18

I reinstalled Windows 11 Pro on `ObiPC` on 2026-09-18 after corrupting the previous installation, and brought the machine back to the state the [2026-09-11 join](ObiPC%20Workstation%20Join%20-%202026-09-11.md) and the [2026-09-12 restriction work](ObiPC%20Restricted%20User%20Setup%20-%202026-09-12.md) had left it in. The domain side survived untouched: the computer object, its organisational unit, the two role groups, the five policies that target the machine, and the directory controls on `IK-user` all still held, so this record is about the half that lives on the disk. The hardware record is [ObiPC specifications](../../../../Infrastructure/Hardware/ObiPC_Specs.md).

I did not diagnose the corruption before reinstalling, so there is no root cause here. Windows reported install time 5:30 PM, which is when the setup finished writing the image.

## What the reinstall took with it

Everything the domain pushes came back on its own at the first policy refresh. Everything I had put on the machine by hand did not:

| Lost with the disk | Restored by | Time |
|---|---|---|
| OpenSSH Server, key-only, and the network profile | `Bootstrap-ObiPC.ps1`, run at the keyboard | 5:51 PM |
| Domain membership and the machine password | Offline domain join with `/reuse` against the existing object | 5:57 PM |
| SSH Manager trust, since the host keys were regenerated | Re-enrolment of all three key types | 6:00 PM |
| Time zone, which the out-of-box setup left on Pacific | `Set-TimeZone` to Eastern | 5:59 PM |
| Google Chrome and Visual Studio Code, machine-wide | Vendor installers, signatures checked | 6:00 PM |
| Remote Desktop and its scoped firewall rules | Same five sources as the 2026-09-12 change | 6:01 PM |
| The `ObiPC Session Limit` scheduled task and its state folder | Re-registered as SYSTEM, one-minute repetition, then **removed again at 6:36 PM by decision**, see below | 6:03 PM |
| `C:\Dev`, the developer carve-out path | Created, `Users` modify | 6:02 PM |
| Microsoft Entra hybrid join | Cloud Sync exported the new certificate on its own schedule; a forced `Automatic-Device-Join` run then completed it | 6:29 PM |
| The Action1 agent | Pushed by Action1 Deployer from `HQ-MGT01` once I took `ObiPC` off its exclusion list | 6:58 PM |

The `D:` volume, `Storage`, came through the reinstall intact and still empty at 466 GB.

## Out-of-box setup

*Set up for work or school*, *Sign-in options*, *Domain join instead*, the same path as the first build, which creates a plain local account and never touches a Microsoft account. The local account is `local-obipc` again, with the password already in my password manager, so the SSH Manager entry stayed true without an edit. Secure Boot was already on in the firmware from 2026-09-11, so this install ran with it on from the start; the bootstrap readback confirmed it.

The bootstrap script is the unchanged per-machine copy in [`Scripts/Bootstrap-ObiPC.ps1`](../../Scripts/Bootstrap-ObiPC.ps1). Its report block read: TPM present and ready, Secure Boot on, Windows 11 Pro build 26200, Ethernet profile Private, `sshd` running and automatic, password authentication off and the key installed, name already `ObiPC`, address `192.168.60.102`, gateway `192.168.60.1`, DNS `192.168.65.10` and `192.168.65.11`, and the domain resolving. Same address as before because the DHCP lease follows the adapter. I compared the ED25519 fingerprint the script printed on the console with the one `ssh-keyscan` returned to my workstation before trusting the host, and they matched.

## Rejoin without a domain administrator password

Same offline join as both earlier workstations. `HQ-DC01` provisioned the package in machine context through the guest agent, into `OU=Standard,OU=Workstations` with `/reuse`, which reset the existing object's machine password rather than creating a second object: `Successfully provisioned [ObiPC]`, 6404 bytes, at 5:55:55 PM. This time the package travelled straight from the controller to my workstation through the Proxmox API file read, then to `ObiPC` with `scp`, because the key the bootstrap installs is my own workstation key. It sat in a mode-700 directory here and in `C:\Windows\Temp` there, and its SHA-256 matched on all three machines before I applied it. `djoin /requestODJ` returned *The provisioning request completed successfully. A reboot is required.* I then overwrote and deleted the copy on the workstation, overwrote and deleted both the package and its base64 form on the controller, and shredded the copy here.

`Restart-Computer` at 5:56:33 PM, never a power cut, and port 22 answered again at 5:57:38 PM. The controller recorded the join as `pwdLastSet` 5:57:37 PM on `CN=OBIPC,OU=Standard,OU=Workstations`.

## Verification

From the workstation:

| Check | Result |
|---|---|
| Domain membership | `PartOfDomain True`, `ad.alphasecunited.com` |
| Secure channel | `Test-ComputerSecureChannel` True; `nltest /sc_verify` `NERR_Success` against `HQ-DC01` |
| Site | `HQ` |
| Time source | `HQ-DC01.ad.alphasecunited.com` |
| Applied computer policy | `C-WKS-ObiPC-OnlineLogon`, `C-WKS-ObiPC-AppControl`, `C-WKS-Action1-Deployer-Network`, `C-CMP-LAPS`, `C-WKS-LocalAdmins`, `Default Domain Policy` |
| Local `Administrators` | `ALPHASEC\ADM-T2-WorkstationAdmins`, `ALPHASEC\Domain Admins`, `ObiPC\Administrator`, `ObiPC\local-obipc` |
| LAPS client policy | backup directory 2, Active Directory |
| AppLocker effective policy | Exe enforced 13 rules, Msi enforced 3, Appx enforced 3, Script audit 11; identical to 2026-09-12 |
| Secure Boot | True |
| BitLocker on `C:` | Off, as before; still a baseline decision |
| OS | Windows 11 Pro 25H2, build 26200.9457, activated |

From `HQ-DC01`:

| Check | Result |
|---|---|
| Object | `CN=OBIPC,OU=Standard,OU=Workstations`, `Windows 11 Pro 10.0 (26200)`, `ObiPC.ad.alphasecunited.com` |
| LAPS | `msLAPS-EncryptedPassword` present, expiry moved to 2026-10-18 at 5:57:38 PM, so the built-in `Administrator` password rotated within a second of the first policy refresh |
| `userCertificate` | one certificate, issued 5:57:40 PM, the new self-signed certificate for the hybrid join; the 2026-09-11 certificate is gone |
| `APP-EntraCloudSync-Devices` | still a member |
| DNS | `ObiPC` A record `192.168.60.102`, unchanged |

## SSH Manager

A reinstall regenerates the host keys, so the three lines SSH Manager held for `192.168.60.102` were stale and every connection would have failed *Host denied*. On `docker-blue` I removed those lines from `/state/ssh/known_hosts` in the `mcp-ssh-manager` container and appended a fresh `ssh-keyscan` of all three types, RSA, ECDSA and ED25519, then read the enrolled ED25519 fingerprint back and matched it against the console. `ssh_execute` against `obipc` then returned `ObiPC`, `obipc\local-obipc`, and the domain.

One trap: `ssh-keyscan` on `docker-blue` writes its `# host:port banner` comment lines to standard output, so a line count that expects exactly three key lines has to filter on the address first. My first attempt aborted on eight lines for that reason, and my second aborted because the machine was mid-reboot and returned nothing. Neither attempt changed the file.

## Session limit task, and a bug it had all along

The task and its state folder are local, so both were gone. I copied [`Scripts/Limit-ObiPCUserSession.ps1`](../../Scripts/Limit-ObiPCUserSession.ps1) to `C:\Program Files\ObiPC-SessionLimit\`, recreated `C:\ProgramData\ObiPC-SessionLimit` with inheritance off and only SYSTEM and Administrators granted, and registered `ObiPC Session Limit` as SYSTEM with a one-minute repetition, a five-minute execution limit, and *ignore new instance*.

The first run returned exit code 1 and wrote no log. Nobody was signed in, and in that case `query.exe user` prints *No User exists for \** to standard error. The script sets `$ErrorActionPreference = 'Stop'`, which turns that stderr line into a terminating `NativeCommandError` before the script reaches its own guard, so every tick on an idle machine died. On 2026-09-12 `IK-user` was signed in for the entire rollout, which is why the task always read result 0 then. I changed the script to relax the preference around that one call and to treat a non-zero exit from `query.exe` as no sessions, redeployed it with a matching SHA-256, and the next scheduled tick at 6:04:30 PM returned 0. The repo copy carries the fix.

### Removed the same evening

After the rebuild I decided to drop the session limit rather than keep it. At 6:36 PM I unregistered `ObiPC Session Limit`, removed `C:\Program Files\ObiPC-SessionLimit` with the script in it, and removed the empty `C:\ProgramData\ObiPC-SessionLimit`. Readback: the task no longer exists and neither folder is present. `C:\Dev` stays. The script remains in the repository as the versioned reference, with the idle-machine fix, in case the control comes back. The directory-side backstop for the same intent, `logonHours` of 7 AM to 11 PM on `IK-user`, is untouched by this and still refuses a sign-in outside those hours; whether it goes too is a separate decision.

## Time zone

The out-of-box setup left the machine on Pacific time, three hours behind the controllers, which the first verification showed as a 2:59 PM local clock against a 5:59 PM domain clock. The session-limit window is enforced in local time on purpose, so on Pacific the 8 AM to 10 PM window would have run 11 AM to 1 AM Eastern. `Set-TimeZone -Id 'Eastern Standard Time'` fixed it and the clock read 5:59:54 PM straight after. I did not check the time zone on 2026-09-11 and the record from that day does not say what it was; the restriction record's verified window on 2026-09-12 implies it was already Eastern then.

## Applications and Remote Desktop

Chrome came from the enterprise MSI and Visual Studio Code from the system installer, both fetched with `curl.exe` and checked with `Get-AuthenticodeSignature` before running: `Valid`, signed by Google LLC and Microsoft Corporation respectively. Installed versions are Chrome 153.0.8010.53 and Visual Studio Code 1.138.0, both under `Program Files` where the AppLocker baseline trusts them. Installers removed afterwards. `winget` was not tried, given the 2026-09-12 finding that it fails in a non-interactive session on this machine.

Remote Desktop went back exactly as the [2026-09-12 change](Domain%20Machine%20RDP%20Enablement%20-%202026-09-12.md) left it: `fDenyTSConnections` 0, `UserAuthentication` still 1, `RemoteDesktop-UserMode-In-TCP` and `-UDP` enabled with the remote address list `192.168.10.0/24`, `192.168.50.0/24`, `192.168.40.179`, `192.168.40.39`, and `10.6.0.0/24`, the shadow rule left disabled, `TermService` automatic and running, listeners on 3389 for IPv4 and IPv6.

## Hybrid join

Completed at 6:29:07 PM, event 306 *Automatic registration Succeeded*, and this time without provisioning on demand. On 2026-09-11 I had provisioned the device by hand after fourteen minutes and said I would give the scheduler thirty minutes next time. I did, and it was enough for the export but not for the join itself: between 5:59 PM and 6:28 PM the registration log showed only event 420, *Unable to acquire Kerberos ticket*, from the Kerberos-based path this build tries first and this forest does not support, with no attempt at the classic path behind it. Those were the lightweight `Device-Sync` retries, not the full task. When I started `Automatic-Device-Join` by hand at 6:29:00 PM it ran the full sequence: pre-checks (331), the Kerberos attempt failing (420, 304), then the classic join request sent (103), answered (104), and completed (105, 306), seven seconds end to end.

`dsregcmd /status` afterwards:

| Field | Value |
|---|---|
| `AzureAdJoined` | YES |
| `DomainJoined` | YES |
| `DeviceId` | equal to the computer object's `objectGUID` on `HQ-DC01`, so the workstation bound to the device record it already had in the tenant rather than creating a second one |
| `KeyProvider` | Microsoft Platform Crypto Provider, `TpmProtected` YES |
| Device certificate | valid 2026-09-18 to 2036-09-18 |
| `AzureAdPrt` | NO, expected with nobody signed in |

That equality is the reason `/reuse` matters for a rebuild. Hybrid join derives the tenant's device id from the on-premises object GUID, so keeping the object keeps the identity; a deleted and recreated computer object would have produced a new GUID, a new device in the tenant, and a stale one to clean up.

What I still do not know is whether the scheduler would have completed the join on its own at the next full task run, which fires at sign-in and on a schedule I did not measure. The export side is settled: Cloud Sync picked up a changed `userCertificate` on an existing device within thirty minutes with no help. Next rebuild, force the task after the export rather than waiting on it.

## Open

- **Action1 agent, restored at 6:58 PM, and a prediction I got wrong.** The agent download URL is withheld and not in my password manager, so I could not reinstall it from here, and the Deployer on `HQ-MGT01` was skipping the machine: its 6:30 PM cycle enumerated all five computers and queued operations for four, because `ObiPC.ad.alphasecunited.com` was on the named-computer exclusion list, enabled, written 11:43 PM on 2026-09-12. That was the fix from [Deployer Health Check Blocked to ObiPC](../../../Action1/Documentation/Troubleshooting/Deployer%20Health%20Check%20Blocked%20to%20ObiPC%20-%202026-09-12.md), applied that night and not recorded as applied until today. I advised leaving the exclusion in place and installing by hand, on the reasoning that the push would use the same VLAN 65 to VLAN 60 remote service control path intrusion prevention blocks. I removed it from the exclusion list in the console instead, at 6:58 PM, and the Deployer did not wait for its hourly cycle: the configuration landed on `HQ-MGT01` at 6:58:16 PM, and in the same second its log shows the `admin$\Action1` share created on `ObiPC`, the updater and the 6.0.664 package copied, the update service created, and at 6:58:21 PM *The agent has been installed successfully*. On `ObiPC`: `A1Agent` running as `LocalSystem`, product `Action1 Agent 6.0.664.1`, and `rules.json` and `advanced_settings.json` written at 6:58:19 and 6:58:20 PM, which the agent only gets from the cloud. So the push path works. Whether the routine health check still trips the intrusion signature every cycle, and whether the exclusion should go back on now that the agent is in, is recorded in the troubleshooting record.
- **Ventoy installer stick.** Was still plugged in as `E:` and `F:` at the time of the volume readback; removed later the same evening.
- **Git, Node.js, Python**, the OneDrive path decision, the Script audit review, RSAT, and the BitLocker baseline are unchanged from before the rebuild and stay in the [platform TODO](../TODO.md).
