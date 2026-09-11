# ObiPC Workstation Join

**Created:** 2026-09-11  
**Last updated:** 2026-09-11

`ObiPC` is the first physical machine on the domain and the first workstation meant for people rather than for proving a policy. Its hardware is in [ObiPC specifications](../../../../Infrastructure/Hardware/ObiPC_Specs.md). Physical machines take the names I give them, one at a time; the `HQ-` scheme stays with the virtual servers and the test workstation.

## Placement

Secure Client, VLAN 60, which the network design reserves for every end-user PC. I moved the switch port to VLAN 60 before the first boot, and the machine took `192.168.60.102` from DHCP with the two domain controllers as resolvers, which that network has handed out since 2026-09-09. `Allow Workstations to AD` already permits the domain port set from this network to the identity plane, and all seven ports I probed on `HQ-DC01` answered before the join. Outbound HTTPS works, which the hybrid join needs.

## Two things that differ from HQ-WS001

**No guest agent, so OpenSSH first.** A physical machine has no `qm guest exec`, and every later step needed a way in. [`Scripts/Bootstrap-ObiPC.ps1`](../../Scripts/Bootstrap-ObiPC.ps1), the per-machine copy of [`Bootstrap-Workstation.ps1`](../../Scripts/Bootstrap-Workstation.ps1), ran once from an elevated PowerShell after the out-of-box setup: TPM and Secure Boot readback, network profile to Private, the OpenSSH Server capability (with a `winget` fallback, since the capability never installed on `HQ-WS001`), sshd automatic and started, the inbound rule on every profile, the SSH Manager public key in `administrators_authorized_keys`, password authentication off, and a report block. The capability installed first time here. Each physical machine gets its own copy of that script in `Scripts/`, so the folder is the record of exactly what ran where.

**The join package travelled over SSH, not a virtual disc.** Same offline domain join as before, so no domain administrator password was typed, passed, or logged anywhere. `HQ-DC01` provisioned the package in machine context through the guest agent, into `OU=Standard,OU=Workstations` with `/reuse`. I copied it controller to `ubuntu-dev` to workstation with `scp`, in a mode-700 directory, applied it with `djoin /requestODJ`, then overwrote and deleted the copy on the workstation, shredded the copy on `ubuntu-dev`, and overwrote and deleted the copy on the controller. The package is single use and dead after the join, but it is still a machine password and was treated as one.

During the out-of-box setup I chose *Set up for work or school*, then *Sign-in options*, then *Domain join instead*, which creates a plain local account and joins nothing. Signing in there with my Microsoft 365 account would have registered the machine as a cloud-joined device and got in the way of the hybrid join. The local account is `local-obipc`, its password in my password manager, and it is the account SSH Manager uses.

## Sequence, all 2026-09-11 Eastern

| Time | Step | Result |
|---|---|---|
| before 4:00 AM | bootstrap script | TPM present and ready, Secure Boot off, OpenSSH running key only, name already `ObiPC`, address `192.168.60.102`, gateway `.60.1`, DNS `.65.10` and `.65.11`, domain resolves |
| 4:02 AM | host key check | fingerprint from `ssh-keyscan` matched the one the script printed on the console before I trusted it |
| 4:05:16 AM | provision on `HQ-DC01` | `Successfully provisioned [ObiPC]`, object `CN=OBIPC,OU=Standard,OU=Workstations`, package 6404 bytes |
| 4:05:47 AM | apply on workstation | `The provisioning request completed successfully. A reboot is required` |
| 4:05:58 AM | `Restart-Computer` over SSH | graceful, never a power cut |
| 4:06:12 AM | back up | port 22 answered ten seconds after the restart was issued |
| 4:06:58 AM | verification | below |

## Verification

From the workstation over SSH:

| Check | Result |
|---|---|
| Domain membership | `PartOfDomain True`, `ad.alphasecunited.com` |
| Secure channel | `Test-ComputerSecureChannel` True; `nltest /sc_verify` `NERR_Success` against `HQ-DC01` |
| Site | `HQ` |
| Time source | `HQ-DC02.ad.alphasecunited.com`, offset 1.2 s and closing, after a forced resync; it read `Local CMOS Clock` in the first minute because the time service had only just started |
| Applied policy | `C-CMP-LAPS`, `C-WKS-LocalAdmins`, `Default Domain Policy` |
| Local `Administrators` | `ALPHASEC\ADM-T2-WorkstationAdmins`, `ALPHASEC\Domain Admins`, `ObiPC\Administrator`, `ObiPC\local-obipc` |
| LAPS client policy | backup directory 2, Active Directory |
| Machine Kerberos tickets | TGT plus `ldap`, `HOST`, and `netlogon` service tickets for both controllers |

From `HQ-DC01`:

| Check | Result |
|---|---|
| Object | `CN=OBIPC,OU=Standard,OU=Workstations`, `Windows 11 Pro 10.0 (26200)`, `ObiPC.ad.alphasecunited.com` |
| LAPS | `msLAPS-EncryptedPassword` populated 4:06:31 AM, expiry 2026-10-11, so the built-in `Administrator` password rotated within twenty seconds of the first policy refresh |
| `userCertificate` | present, the self-signed certificate the hybrid join needs |
| `APP-EntraCloudSync-Devices` | `HQ-WS001`, `OBIPC` |

The Tier 2 group is in local Administrators by policy, as on `HQ-WS001`. Unlike that machine, a second local administrator remains: `local-obipc`, the account created at setup. The local-administrators policy adds the tier group and does not strip local users, so this account stays. It is the SSH management account, so that is intended, and its password is in the password manager rather than under LAPS. LAPS covers the built-in `Administrator` only.

## SSH Manager

Added as server `obipc`, user `local-obipc`, platform `windows`, in the service's server definitions on `docker-blue`, and the service recreated so it read the new environment. The first health check failed with *Host denied (verification failed)* although the ed25519 key was enrolled. The client library negotiates a host key type with the Windows server that is not necessarily ed25519, and the verifier compares the presented key with every enrolled key for that host, so a single-type enrolment can fail. Enrolling all three types the server offers, `rsa`, `ecdsa` and `ed25519`, fixed it, and the three existing Windows servers had all three enrolled from the start. `hostname; whoami` then returned `ObiPC`, `obipc\local-obipc`, and the domain through the tool. Note for that platform: the tool wraps the command in PowerShell 5.1, so `&&` is invalid; separate statements with `;`.

## Hybrid join

Added to the device scope group at 4:07 AM. The `Automatic-Device-Join` task on the workstation then reported two failures per run: `0x801c03f3` at the join phase, which is the device not yet existing in the tenant, the same state `HQ-WS001` sat in before its export; and event 420, *Unable to acquire Kerberos ticket*, from the Windows Server 2025 Kerberos-based hybrid join path that this Windows 11 build tries first, which needs `EnableKerbHaadj` on the controllers and is not something this forest uses. The classic path is the one that completes once Cloud Sync has exported the computer.

The scheduled cycle had not exported it after fourteen minutes and six task runs, so at about 4:20 AM I provisioned the computer on demand from the Cloud Sync configuration, object type Devices, by distinguished name. All four stages passed and the export read *Computer was created in Microsoft Entra ID*, `deviceTrustType ServerAd`, `deviceOSType Windows`, display name `ObiPC`, with the source anchor and the certificate carried across. The next `Automatic-Device-Join` run, started at 4:21:47 AM, logged *Automatic registration Succeeded* (event 306), and `dsregcmd /status` then read:

| Field | Value |
|---|---|
| `AzureAdJoined` | YES |
| `DomainJoined` | YES |
| `DeviceId` | the id Entra reported for the created object, so the workstation bound to the right record |
| `KeyProvider` | Microsoft Platform Crypto Provider, `TpmProtected` YES |
| Device certificate | valid 2026-09-11 to 2036-09-11 |

Two runs in a row have now needed provision on demand before a device joined, on `HQ-WS001` and here. Either the scheduled cycle does not pick up a computer that enters the scope group between cycles as quickly as a user, or it does and I have not waited long enough; fourteen minutes is the longest I have watched. Next workstation, I will let the scheduler run for thirty minutes before provisioning on demand, and record which it was.

## Result

`ObiPC` is a domain-joined, LAPS-managed, Microsoft Entra hybrid joined physical workstation on Secure Client, reachable through SSH Manager, with policy placing the Tier 2 group in its local Administrators. Any staff account in the directory can sign in at its keyboard and reach Microsoft 365 with the same password.

## First sign-in, observed

I signed in at the keyboard as `ALPHASEC\DK-user`, my own directory account, rather than `testuser`. Read from the machine afterwards: Security event 4624, logon type 2 (interactive), `ALPHASEC\DK-user`, package Negotiate, at 9:56:59 AM on 2026-09-11; the profile `C:\Users\DK-user` created at 9:57:00 AM; a type 11 logon at 9:59:30 AM, which is the cached-credential unlock; and `Win32_ComputerSystem.UserName` reading `ALPHASEC\DK-user` while I was on the desktop. The account is not in the local `Administrators` group, which is the tiered model holding: daily work as a standard user, elevation through `DK-t2`. That closes the sign-in item.

## Secure Boot

Turned on in the BIOS at about 10:19 AM, Standard mode with the Microsoft keys, Windows UEFI Mode. Read back from the machine after the reboot: `Confirm-SecureBootUEFI` True, policy publisher `77fa9abd-0359-4d32-bd60-28f4e78f784b`, which is the Microsoft Windows production policy, last boot 10:19:44 AM. The domain secure channel and the hybrid join both survived the firmware change, and the TPM reports ready.

BitLocker is off on `C:`. Nothing today asked for it, and it is not turned on here, but a physical machine that leaves the building is where it matters; a decision for the workstation baseline rather than this record.

## Open

Nothing. Closed 10:25 AM on 2026-09-11. BitLocker for physical workstations is a baseline decision, noted above.
