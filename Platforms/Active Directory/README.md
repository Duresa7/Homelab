# Active Directory

**Created:** 2026-09-09  
**Last updated:** 2026-09-18

I run the `ad.alphasecunited.com` forest on two Windows Server 2025 Standard domain controllers in IDENTITY-A, VLAN 65, on Galaxy's `grey-server`. This is a new forest built on 2026-09-09. It shares no state with the Windows Server work I retired to the archive on 2026-09-06, and none of those older records describe this build.

## Current State

| Item | Current value |
|---|---|
| Deployment status | Operational. Replication, DNS, policy, LAPS, and external time verified 2026-09-09 |
| Forest and domain | `ad.alphasecunited.com`, NetBIOS `ALPHASEC` |
| Functional level | `Windows2016Forest` and `Windows2016Domain` |
| Domain controllers | `HQ-DC01` at `192.168.65.10` (VM 301) and `HQ-DC02` at `192.168.65.11` (VM 302) |
| Operations masters | All five roles on `HQ-DC01`: schema, domain naming, PDC, RID, infrastructure |
| Global catalog | Both controllers |
| Site | `HQ`, with `192.168.65.0/24`, `192.168.50.0/24`, and `192.168.60.0/24` mapped to it |
| Member server | `HQ-MGT01` at `192.168.65.12` (VM 303) in `OU=Management,OU=Servers` |
| Windows Admin Center | [Gateway on HQ-MGT01](../Windows%20Admin%20Center/README.md), file version `2.7.21.5`, HTTPS 443; five shared connections and AD/DNS extensions verified, browser sign-in confirmed 2026-09-12; all five WAC target queries and elevated Kerberos HTTPS sessions verified |
| Workstations | `HQ-WS001` at `192.168.65.20` (VM 310), Windows 11 Pro 25H2, activated 2026-09-10, Microsoft Entra hybrid joined 2026-09-10; `ObiPC`, physical, Secure Client VLAN 60 by DHCP, Windows 11 Pro 25H2, joined and Microsoft Entra hybrid joined 2026-09-11, Windows reinstalled and rejoined to the same computer and device objects 2026-09-18. Both in `OU=Standard,OU=Workstations` |
| UPN suffix | `alphasecunited.com` added alongside the default |
| AD Recycle Bin | Enabled |
| DNS zones | `ad.alphasecunited.com` (domain scope), `_msdcs.ad.alphasecunited.com` (forest scope), `65.168.192.in-addr.arpa` (forest scope). All primary, AD-integrated, secure dynamic update only |
| DNS forwarder | `192.168.65.1` |
| Scavenging | Enabled, 7-day no-refresh and 7-day refresh |
| Default password policy | 8 characters (lowered from 14 on 2026-09-10, accepted as the standing minimum), complexity on, history 24, no expiry, lockout 10 attempts for 15 minutes |
| Fine-grained policy | `PSO-Admins`, precedence 10, 14 characters (lowered from 20 on 2026-09-10 for a testing window; restore to 20), 365-day maximum age, lockout 5 attempts for 30 minutes |
| Time source | `HQ-DC01` synchronises from `time.cloudflare.com` at stratum 4; the other two follow the domain hierarchy |
| Remote access | `hq_dc01`, `hq_dc02`, `hq_mgt01`, and `obipc` in SSH Manager over OpenSSH on port 22, key only; `HQ-WS001` through the QEMU guest agent. RDP enabled on all five since 2026-09-12, Network Level Authentication required, host firewall scoped to Trusted VLAN 10, Secure VLAN 50, `192.168.40.179`, `192.168.40.39`, and the `10.6.0.0/24` Management Access VPN |
| Entra Cloud Sync agent | Version 1.1.2334.0 on `HQ-MGT01`, registered 2026-09-10, running as gMSA `pGMSA_e6620264$` |
| Entra Cloud Sync configuration | `ad.alphasecunited.com`, AD to Microsoft Entra ID, password hash sync on, device sync on, scoped to `APP-EntraCloudSync-Users` and `APP-EntraCloudSync-Devices`; first cycle 2026-09-10 created `IK-user`, `AH-user`, `testuser` and the users group in the tenant; `HQ-WS001` provisioned on demand the same day; `DK-user@alphasecunited.com` soft-matched onto its directory account at 10:50 PM the same day, object id unchanged |

## Tiered Administration

The directory is laid out for a tiered administrative model. Tier 0 covers the forest itself, Tier 1 the member servers, and Tier 2 the workstations. Thirty-three organisational units carry that split, and both computer and user redirection point at `Staging` so a default-location join never lands an object in a container that no policy reaches.

| Group | Scope | Purpose | Members (administrative groups verified 2026-09-12) |
|---|---|---|---|
| `ADM-T0-DomainAdmins` | Global | Nested into `Domain Admins` | `DK-t0`, `DK-user` |
| `ADM-T1-ServerAdmins` | Global | Local administrator on member servers through Group Policy | `DK-user` |
| `ADM-T2-WorkstationAdmins` | Global | Local administrator on workstations through Group Policy | `DK-t2`, `DK-user` (added 2026-09-11, my decision; see [Owner Account Workstation Admin](Documentation/Change%20Records/Owner%20Account%20Workstation%20Admin%20-%202026-09-11.md)); `APP-Action1-LocalAdmins` nested 2026-09-12 |
| `APP-Action1-LocalAdmins` | Global | Action1 workstation administration through the Tier 2 group; separately added to local Administrators on `HQ-MGT01` | `svc-action1-deploy`; no Domain Admin or Tier 1 membership |
| `ROL-Staff` | Global | Role group for standard staff accounts | `IK-user`, `AH-user`, `testuser`, `DK-user` |
| `APP-EntraCloudSync-Users` | Global | Scope group for Entra Cloud Sync | `IK-user`, `AH-user`, `testuser`, `DK-user` |
| `APP-EntraCloudSync-Devices` | Global | Scope group for Entra Cloud Sync device sync; a computer not in a scope group is never exported | `HQ-WS001`, `OBIPC` |
| `ROL-ObiPC-Restricted` | Global | Principal on the `ObiPC` AppLocker allowlist and Settings lockdown, enforced 2026-09-12 | `IK-user` |
| `ROL-ObiPC-Unrestricted` | Global | Holds the allow-all AppLocker rule on `ObiPC`, so restriction lands on one account rather than the machine | `DK-user`, `AH-user`, `testuser` |

`Domain Admins` holds the built-in `Administrator` account and `ADM-T0-DomainAdmins`, nothing else. `DK-t0` is in `Protected Users` and is flagged as sensitive and not delegated. The built-in `Administrator` is the break-glass account and is not used for daily work.

I expanded DK-user to all three administrative tiers on 2026-09-12, by my explicit decision. Both controllers resolve its Domain Admin membership, and fresh sessions on all five Windows targets have elevated administrator tokens. This account also administers WAC, with gateway-session-only target queries verified over WinRM HTTPS. Its resultant password policy is `PSO-Admins`. See [Owner Domain Administration](Documentation/Change%20Records/Owner%20Domain%20Administration%20-%202026-09-12.md).

## Group Policy

| Policy | Status | Linked to |
|---|---|---|
| `C-CMP-LAPS` | All settings enabled | `Servers`, `Workstations` |
| `C-SRV-LocalAdmins` | All settings enabled | `Servers` |
| `C-WKS-LocalAdmins` | All settings enabled | `Workstations` |
| `C-WKS-Action1-Deployer-Network` | Domain-profile SMB, RPC endpoint mapper, and service RPC only from `192.168.65.12`; applied on both workstations 2026-09-12 | `Standard,Workstations` |
| `C-WKS-ObiPC-AppControl` | AppLocker (Exe/Msi/Appx enforced, Script audit; since 2026-09-18 48 executable rules, 44 of them denies for the restricted group, no executable allow of its own for that group, and 23 writable-folder exceptions; since 2026-09-19 seven packaged-app rules, denying the Microsoft Store, the Store purchase app, the Xbox app and App Installer for that group), loopback Merge, restricted-user UAC prompt for credentials. `AppIDSvc` is set Automatic on the machine itself, not by this policy | `Standard,Workstations`, filtered to `OBIPC` |
| `U-WKS-ObiPC-Restricted` | Settings `showonly:` allowlist, Control Panel allowlist, power menu removed, MMC snap-ins blocked, Store removed, registry tools off, Chrome and Edge extensions blocked and executable downloads blocked in both; widened 2026-09-18 | `Standard,Workstations`, filtered to `ROL-ObiPC-Restricted` |
| `C-WKS-ObiPC-Lockdown` | Recovery environment tools require an administrator account, legacy reset off, sign-in screen power button removed, sideloading and App Installer channels closed, workplace join blocked, 15-minute lock, AutoPlay off, machine-wide proxy, Windows Security overrides off, long paths on; created 2026-09-18, and kept to settings that do not restrict other accounts after the [recovery-menu wipe](../../Security/Incidents/Active%20Directory/ObiPC%20Wiped%20from%20the%20Recovery%20Menu%20-%202026-09-18.md) | `Standard,Workstations`, filtered to `OBIPC` |
| `Default Domain Policy` | All settings enabled | domain root |
| `Default Domain Controllers Policy` | All settings enabled | `Domain Controllers` |

The two local-administrator policies use Group Policy Preferences local users and groups. They add the matching tier group to local `Administrators` and leave existing local accounts in place, so a server gets `ADM-T1-ServerAdmins` and a workstation gets `ADM-T2-WorkstationAdmins`. ObiPC kept its setup account. Both halves are proven on a live machine: `HQ-MGT01` carries the Tier 1 group and `HQ-WS001` carries the Tier 2 group, each placed there by policy rather than by hand.

The dedicated `svc-action1-deploy` account is in `OU=Service Accounts,OU=Tier 2,OU=Admin`, is marked not delegatable, and uses the existing workstation-administration policy through its dedicated group. Its local-administrator membership on `HQ-MGT01` is specific to that host. The [Action1 deployment record](../Action1/Documentation/Change%20Records/AD%20Deployer%20Preparation%20-%202026-09-12.md) owns the installation, account, firewall, and verification details.

## Windows LAPS

The schema is extended for Windows LAPS, confirmed by the presence of `msLAPS-EncryptedPassword`. Computers hold self-write permission on the `Servers`, `Workstations`, and `Staging` computer containers. `C-CMP-LAPS` backs passwords to Active Directory with 20 characters, a 30-day rotation, encryption on, and a post-authentication reset.

`HQ-MGT01`, `HQ-WS001`, and ObiPC (`OBIPC`) are managed and hold stored passwords, expiring 2026-10-09, 2026-10-10, and 2026-10-11 respectively. Retrieve it with `Get-LapsADPassword -Identity HQ-MGT01 -AsPlainText`. The domain controllers are not LAPS-managed, which is expected: a domain controller has no local account database to manage.

## Credentials

Every account here is stored in my password manager. No password, DSRM password, or recovery key appears in this repository. Once a machine becomes LAPS-managed its stored local administrator password is authoritative and the password manager entry for that machine is stale.

## Open Items

- `IK-user` is pinned to `OBIPC` by `userWorkstations` and carries `logonHours` of 7 AM to 11 PM. Those hours were the backstop to the ObiPC session-limit task, which I removed on 2026-09-18 after the rebuild; the hours now stand alone and are the only sign-in window control left. Widen `userWorkstations` before that account can use any other domain machine. Review the ObiPC AppLocker Script audit log before enforcing that collection, and decide the OneDrive per-user path exception. See [ObiPC Restricted User Setup](Documentation/Change%20Records/ObiPC%20Restricted%20User%20Setup%20-%202026-09-12.md). On 2026-09-18 he wiped the machine from the recovery menu, which Windows 11 allows with no credentials; the recovery environment is now disabled and kept disabled by a SYSTEM task, every recovery tool requires an administrator account, and the sign-in screen, power menu, Settings, Control Panel, MMC and the script and recovery binaries are closed to him. The developer carve-out is closed: his group has no executable allow of its own, so Action1 is the only way software reaches him, and Chrome and Edge refuse executable downloads for him. Other accounts on the machine are unaffected apart from the recovery and sign-in screen controls. The user-side half has not been observed on his session yet. See [ObiPC Recovery and Settings Lockdown](Documentation/Change%20Records/ObiPC%20Recovery%20and%20Settings%20Lockdown%20-%202026-09-18.md).

- I still need to observe my first elevation as `DK-user` on ObiPC after the 2026-09-11 group change, following a sign-out and sign-in.
- Hybrid identity is proven end to end as of 2026-09-10: `IK-user`, `AH-user` and `testuser` are in the tenant on Business Basic, `HQ-WS001` is Microsoft Entra hybrid joined, and `testuser` signs in to Microsoft 365 with its directory password. `testuser` was rotated off the break-glass value at 5:13 PM on 2026-09-10; the other four shared-password accounts and `PSO-Admins` are still in their testing state, listed in [Shared Test Password and Admin Policy Relaxation - 2026-09-10](Documentation/Change%20Records/Shared%20Test%20Password%20and%20Admin%20Policy%20Relaxation%20-%202026-09-10.md). My own account `DK-user@alphasecunited.com` is on the directory by soft match since 10:50 PM on 2026-09-10, with its Business Premium seat and mailbox intact and its administrative roles moved to the cloud-only `DK-admin@alphasecunited.com`; mailbox and `HQ-WS001` sign-ins both verified and the record closed; see [Owner Account Soft Match - 2026-09-10](Documentation/Change%20Records/Owner%20Account%20Soft%20Match%20-%202026-09-10.md). See also [Cloud Sync Configuration and First Cycle - 2026-09-10](Documentation/Change%20Records/Cloud%20Sync%20Configuration%20and%20First%20Cycle%20-%202026-09-10.md).
- Neither controller audits credential-validation failures (`Credential Validation` is `Success` only), so a lockout leaves no 4776 trail. Add failure auditing.
- OpenSSH Server will not install on `HQ-WS001`. `Add-WindowsCapability` leaves the capability `NotPresent` and `Get-WindowsCapability -Online` hangs while the servicing stack is busy. Outbound HTTPS from that machine works, so it is not a network path problem. The workstation is therefore not in SSH Manager and is managed through the QEMU guest agent.
- Future WAC targets need WinRM HTTPS, trusted certificates, and delegation from HQ-MGT01 as part of onboarding; the existing administrative group policies cover servers and workstations in their scoped OUs.
- `ObiPC` carried the [Action1 agent](../Action1/README.md) from 2026-09-12, version 6.0.664.1, so software deployment for that machine had a console. The 2026-09-18 operating system reinstall removed it and the Deployer on `HQ-MGT01` pushed it back the same evening once I lifted the console exclusion on `ObiPC`. It is not Intune managed and the two products overlap on software deployment.
- Neither `HQ-WS001` nor `ObiPC` is Intune managed. Both are Microsoft Entra hybrid joined through Cloud Sync device sync and both read `MDM: None`, confirmed against the tenant on 2026-09-11. Whether they should be co-managed is an open decision recorded in the [Microsoft Intune TODO](../Microsoft%20Intune/Documentation/TODO.md).

## Records

- [ObiPC Recovery and Settings Lockdown - 2026-09-18](Documentation/Change%20Records/ObiPC%20Recovery%20and%20Settings%20Lockdown%20-%202026-09-18.md): response to the recovery-menu wipe. Recovery environment disabled and re-disabled on a schedule, administrator credentials required for every recovery tool through the MDM bridge and Group Policy, sign-in screen power button and the restricted user's power menu removed, a new AppLocker policy with 44 denies, 23 writable-folder exceptions and the developer carve-out removed so Action1 is the only install path, browser executable downloads blocked, a `showonly:` Settings allowlist replacing the undocumented `hideonly:` one, Control Panel and MMC allowlists, and the install channels closed. Verified on the machine; user side pending his next sign-in.

- [ObiPC Wiped from the Recovery Menu - 2026-09-18](../../Security/Incidents/Active%20Directory/ObiPC%20Wiped%20from%20the%20Recovery%20Menu%20-%202026-09-18.md): the incident. A standard user reset the machine to factory state from the recovery environment, which requires no authentication for a full wipe on Windows 11. Root cause, timeline from the reset logs, and the corrective action.

- [ObiPC Rebuild and Rejoin - 2026-09-18](Documentation/Change%20Records/ObiPC%20Rebuild%20and%20Rejoin%20-%202026-09-18.md): Windows reinstalled on `ObiPC` after the recovery-menu wipe, rejoined by offline join with `/reuse` against the existing object, SSH Manager host keys replaced, and everything that lived on the disk restored by hand: time zone, Chrome, Visual Studio Code, Remote Desktop scope, and `C:\Dev`; the session-limit task came back with a fix for idle-machine ticks and was then removed by decision the same evening, and the Action1 Deployer pushed the agent back once its exclusion was lifted.

- [Domain Machine RDP Enablement - 2026-09-12](Documentation/Change%20Records/Domain%20Machine%20RDP%20Enablement%20-%202026-09-12.md): Remote Desktop enabled on all five domain machines with Network Level Authentication required, host firewall sources scoped, and three UniFi allow policies into `AlphaSec-Identity`. Interactive sign-on proven on `HQ-WS001`; the other four are verified to the port and logon-right level only. Targets are addressed by IP.

- [ObiPC Restricted User Setup - 2026-09-12](Documentation/Change%20Records/ObiPC%20Restricted%20User%20Setup%20-%202026-09-12.md): AppLocker allowlist, Settings lockdown, daily sign-in window and usage budget, and `userWorkstations` pinning for `IK-user` on `ObiPC`. Enforced and verified on his live session.

- [Staff First Login Password Change - 2026-09-12](Documentation/Change%20Records/Staff%20First%20Login%20Password%20Change%20-%202026-09-12.md): AH-user and IK-user must change their passwords at next domain logon; verified on both controllers. Their password changes remain pending.

- [Owner Domain Administration - 2026-09-12](Documentation/Change%20Records/Owner%20Domain%20Administration%20-%202026-09-12.md)

- [Windows Admin Center deployment - 2026-09-12](../Windows%20Admin%20Center/Documentation/Change%20Records/Deployment%20-%202026-09-12.md)

- [Forest Build - 2026-09-09](Documentation/Change%20Records/Forest%20Build%20-%202026-09-09.md)
- [HQ-WS001 Workstation Join - 2026-09-10](Documentation/Change%20Records/HQ-WS001%20Workstation%20Join%20-%202026-09-10.md)
- [Hybrid Identity Preparation - 2026-09-10](Documentation/Change%20Records/Hybrid%20Identity%20Preparation%20-%202026-09-10.md)
- [Entra Provisioning Agent Install - 2026-09-10](Documentation/Change%20Records/Entra%20Provisioning%20Agent%20Install%20-%202026-09-10.md)
- [Cloud Sync Configuration and First Cycle - 2026-09-10](Documentation/Change%20Records/Cloud%20Sync%20Configuration%20and%20First%20Cycle%20-%202026-09-10.md)
- [Shared Test Password and Admin Policy Relaxation - 2026-09-10](Documentation/Change%20Records/Shared%20Test%20Password%20and%20Admin%20Policy%20Relaxation%20-%202026-09-10.md)
- [Owner Account Soft Match - 2026-09-10](Documentation/Change%20Records/Owner%20Account%20Soft%20Match%20-%202026-09-10.md)
- [ObiPC Workstation Join - 2026-09-11](Documentation/Change%20Records/ObiPC%20Workstation%20Join%20-%202026-09-11.md)
- [Owner Account Workstation Admin - 2026-09-11](Documentation/Change%20Records/Owner%20Account%20Workstation%20Admin%20-%202026-09-11.md)
- [Microsoft Intune](../Microsoft%20Intune/README.md) for device management in the same tenant, including the Apple credentials and why neither workstation here is Intune managed
- [Active Directory guide](../../Guides/Active-Directory.md)
- [Identity NTP and Client DNS - 2026-09-09](../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09.md)
- [Galaxy VMs](../../Operations/Inventory/Galaxy/VMs.md) for VMs 300 through 303 and VM 310
