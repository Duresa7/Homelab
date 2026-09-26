# Active Directory

**Created:** 2026-09-09  
**Last updated:** 2026-09-25

I run the `ad.alphasecunited.com` forest on two Windows Server 2025 Standard domain controllers in IDENTITY-A, VLAN 65, on Galaxy's `grey-server`. I built it on 2026-09-09. It shares no state with the Windows Server work I retired to the archive on 2026-09-06.

## Current State

| Item | Current value |
|---|---|
| Deployment status | Operational. Replication, DNS, policy, LAPS, and external time verified 2026-09-09 |
| Forest and domain | `ad.alphasecunited.com`, NetBIOS `ALPHASEC` |
| Functional level | `Windows2016Forest` and `Windows2016Domain` |
| Domain controllers | `HQ-DC01` at `192.168.65.10` (VM 301) and `HQ-DC02` at `192.168.65.11` (VM 302), both running on 2026-09-24 |
| Operations masters | All five roles on `HQ-DC01`: schema, domain naming, PDC, RID, infrastructure |
| Global catalog | Both controllers |
| Site | `HQ`, with `192.168.65.0/24`, `192.168.50.0/24`, and `192.168.60.0/24` mapped to it |
| Member server | `HQ-MGT01` at `192.168.65.12` (VM 303) in `OU=Management,OU=Servers` |
| Windows Admin Center | [Gateway on HQ-MGT01](../Windows%20Admin%20Center/README.md), file version `2.7.21.5`, HTTPS 443, five shared connections, service running on 2026-09-25 |
| Azure Arc | [HQ-MGT01 only](../Azure%20Arc/README.md), agent `1.67.03504.3207`, `Connected` with a heartbeat at 1:32 AM on 2026-09-25 |
| HQ-WS001 | `192.168.65.20`, VM 310 on grey (8 GiB, 4 vCPU), Windows 11 Pro 25H2, Microsoft Entra hybrid joined 2026-09-10, in `OU=Standard,OU=Workstations`. **Stopped** on 2026-09-24 |
| ObiPC | Physical, Secure Client VLAN 60 by DHCP (`192.168.60.102`), Windows 11 Pro 25H2, joined and hybrid joined 2026-09-11, reinstalled and rejoined to the same objects 2026-09-18, in `OU=Standard,OU=Workstations`. Unreachable on 2026-09-24: UniFi last saw its wired interface at 4:08:53 PM that day |
| `IK-user` | **Disabled** 2026-09-23 at 8:24:48 PM, `Enabled=false` on both controllers. Group memberships, `userWorkstations=OBIPC` and `logonHours` of 7 AM to 11 PM are unchanged. ObiPC rejected two interactive sign-ins with it at 9:26 PM that night |
| UPN suffix | `alphasecunited.com` added alongside the default |
| AD Recycle Bin | Enabled |
| DNS zones | `ad.alphasecunited.com` (domain scope), `_msdcs.ad.alphasecunited.com` (forest scope), `65.168.192.in-addr.arpa` (forest scope). All primary, AD-integrated, secure dynamic update only |
| DNS forwarder | `192.168.65.1` |
| Scavenging | Enabled, 7-day no-refresh and 7-day refresh |
| Default password policy | 8 characters (lowered from 14 on 2026-09-10, accepted as the standing minimum), complexity on, history 24, no expiry, lockout 10 attempts for 15 minutes |
| Fine-grained policy | `PSO-Admins`, precedence 10, 14 characters (lowered from 20 on 2026-09-10 for a testing window; restore to 20), 365-day maximum age, lockout 5 attempts for 30 minutes |
| Time source | `HQ-DC01` synchronises from `time.cloudflare.com` at stratum 4; the other two follow the domain hierarchy |
| Remote access | `hq_dc01`, `hq_dc02`, `hq_mgt01` and `obipc` in SSH Manager over OpenSSH on port 22, key only. `HQ-WS001` runs `sshd` since 2026-09-19, reachable from Secure VLAN 50 only and not in SSH Manager; automation reaches it through the QEMU guest agent. RDP on all five machines since 2026-09-12, Network Level Authentication required, host firewall scoped to Trusted VLAN 10, Secure VLAN 50, `192.168.40.179`, `192.168.40.39`, and the `10.6.0.0/24` Management Access VPN |
| Endpoint management | [Action1](../Action1/README.md) agents on `ObiPC`, `HQ-WS001` and `HQ-MGT01`. Neither workstation is Intune managed (`MDM: None`, 2026-09-11) |
| Entra Cloud Sync agent | Version 1.1.2334.0 on `HQ-MGT01`, registered 2026-09-10, running as gMSA `pGMSA_e6620264$` |
| Entra Cloud Sync configuration | AD to Microsoft Entra ID, password hash sync on, device sync on, scoped to `APP-EntraCloudSync-Users` and `APP-EntraCloudSync-Devices`. `IK-user`, `AH-user`, `testuser`, `DK-user` and both workstations are in the tenant; `DK-user@alphasecunited.com` soft-matched onto its directory account on 2026-09-10 with its object id unchanged, and its roles moved to the cloud-only `DK-admin` |

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
| `ROL-ObiPC-Restricted` | Global | Principal on the `ObiPC` AppLocker allowlist and Settings lockdown, enforced 2026-09-12 | `IK-user`, `testuser` (added 2026-09-19 to test the lockdown from a session; a fixture, to be moved back) |
| `ROL-ObiPC-Unrestricted` | Global | Holds the allow-all AppLocker rule on `ObiPC`, so restriction lands on one account rather than the machine | `DK-user`, `AH-user` |

`Domain Admins` holds the built-in `Administrator` account and `ADM-T0-DomainAdmins`, nothing else. `DK-t0` is in `Protected Users` and is flagged as sensitive and not delegated. The built-in `Administrator` is the break-glass account and is not used for daily work.

I expanded DK-user to all three administrative tiers on 2026-09-12, by my explicit decision. Both controllers resolve its Domain Admin membership, and fresh sessions on all five Windows targets have elevated administrator tokens. This account also administers WAC, with gateway-session-only target queries verified over WinRM HTTPS. Its resultant password policy is `PSO-Admins`. See [Owner Domain Administration](Documentation/Change%20Records/Owner%20Domain%20Administration%20-%202026-09-12.md).

## Group Policy

| Policy | Status | Linked to |
|---|---|---|
| `C-CMP-LAPS` | All settings enabled | `Servers`, `Workstations` |
| `C-SRV-LocalAdmins` | All settings enabled | `Servers` |
| `C-WKS-LocalAdmins` | All settings enabled | `Workstations` |
| `C-WKS-OnlineLogon` | Cached domain passwords disabled, online unlock required, foreground network wait enabled, Hello provisioning and alternative PIN/biometric/picture/FIDO sign-in providers disabled; applied and read back on both workstations 2026-09-19 | `Workstations` |
| `C-WKS-ObiPC-OnlineLogon` | Existing cached-logon and online-unlock settings, matching `C-WKS-OnlineLogon` | `Standard,Workstations`, filtered to `OBIPC` |
| `C-WKS-Action1-Deployer-Network` | Domain-profile SMB, RPC endpoint mapper, and service RPC only from `192.168.65.12`; applied on both workstations 2026-09-12 | `Standard,Workstations` |
| `C-WKS-ObiPC-AppControl` | AppLocker (Exe/Msi/Appx enforced, Script audit). 55 executable rules: 44 denies for the restricted group with 23 writable-folder exceptions (2026-09-18), seven publisher allows for that group (Spotify, Discord, Roblox, Riot Games, Ubisoft, NVIDIA, BattlEye; 2026-09-20), and four path allows. Seven packaged-app rules since 2026-09-19, denying the Microsoft Store, the Store purchase app, the Xbox app and App Installer for that group, loopback Merge, restricted-user UAC prompt for credentials. `AppIDSvc` is set Automatic on the machine itself, not by this policy | `Standard,Workstations`, filtered to `OBIPC` |
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

The steps and completion checks are in the [Active Directory TODO](Documentation/TODO.md).

- Online sign-in: interactive offline sign-in and unlock checks are still open on both workstations.
- ObiPC lockdown: the user-side checks waited on `IK-user`'s session and are blocked while the account is disabled.
- `testuser` is still in `ROL-ObiPC-Restricted` as a test fixture since 2026-09-19.
- The ObiPC AppLocker Script collection is audit-only, and the OneDrive per-user path is undecided.
- The four shared test passwords and `PSO-Admins` at 14 characters are still in their 2026-09-10 testing state.
- Neither controller audits `Credential Validation` failures, so a lockout leaves no 4776 trail.
- The `HQ-WS001` SSH rule is unproven from Jedi PC, and the host is not in SSH Manager.
- My first elevation as `DK-user` on ObiPC after the 2026-09-11 group change is unobserved.
- Future WAC targets need WinRM HTTPS, trusted certificates and delegation from HQ-MGT01 at onboarding.
- Intune co-management of the two workstations is an open decision in the [Microsoft Intune TODO](../Microsoft%20Intune/Documentation/TODO.md).

## Records

- [ObiPC Shutdown Attempt - 2026-09-24](Documentation/Change%20Records/ObiPC%20Shutdown%20Attempt%20-%202026-09-24.md): ObiPC unreachable; no shutdown delivered.
- [ObiPC Sign-In Review - 2026-09-24](../../Security/Assessments/ObiPC%20Sign-In%20Review%20-%202026-09-24.md): only computer-account authentication on the controllers.
- [IK-user Account Disabled - 2026-09-23](Documentation/Change%20Records/IK-user%20Account%20Disabled%20-%202026-09-23.md): account disabled; two rejected sign-ins afterwards.
- [ObiPC Event Review - 2026-09-23](../../Security/Assessments/ObiPC%20Event%20Review%20-%202026-09-23.md): application failures, Group Policy errors, AppLocker blocks and Defender state.
- [ObiPC Domain Sign-in Error - 2026-09-20](Documentation/Troubleshooting/ObiPC%20Domain%20Sign-in%20Error%20-%202026-09-20.md): fixed by correcting the Ethernet port serving ObiPC.
- [ObiPC Publisher Allows - 2026-09-20](Documentation/Change%20Records/ObiPC%20Publisher%20Allows%20-%202026-09-20.md): seven publisher allow rules, Exe rules 48 to 55.
- [LDAPS on the Domain Controllers - 2026-09-20](Documentation/Change%20Records/LDAPS%20on%20the%20Domain%20Controllers%20-%202026-09-20.md): LDAPS certificates from a local authority on each controller.
- [HQ-WS001 SSH Enablement - 2026-09-19](Documentation/Change%20Records/HQ-WS001%20SSH%20Enablement%20-%202026-09-19.md): `sshd` started and a Secure-only path through the gateway.
- [Online Workstation Sign-In - 2026-09-19](Documentation/Change%20Records/Online%20Workstation%20Sign-In%20-%202026-09-19.md): online-only domain sign-in and unlock policy.
- [ObiPC Recovery and Settings Lockdown - 2026-09-18](Documentation/Change%20Records/ObiPC%20Recovery%20and%20Settings%20Lockdown%20-%202026-09-18.md): the response to the recovery-menu wipe.
- [ObiPC Rebuild and Rejoin - 2026-09-18](Documentation/Change%20Records/ObiPC%20Rebuild%20and%20Rejoin%20-%202026-09-18.md): reinstall, offline rejoin and restore.
- [ObiPC Wiped from the Recovery Menu - 2026-09-18](../../Security/Incidents/Active%20Directory/ObiPC%20Wiped%20from%20the%20Recovery%20Menu%20-%202026-09-18.md): the incident.
- [Domain Machine RDP Enablement - 2026-09-12](Documentation/Change%20Records/Domain%20Machine%20RDP%20Enablement%20-%202026-09-12.md): RDP on all five domain machines.
- [ObiPC Restricted User Setup - 2026-09-12](Documentation/Change%20Records/ObiPC%20Restricted%20User%20Setup%20-%202026-09-12.md): the first AppLocker allowlist and Settings lockdown.
- [Staff First Login Password Change - 2026-09-12](Documentation/Change%20Records/Staff%20First%20Login%20Password%20Change%20-%202026-09-12.md): password change at next logon for two staff accounts.
- [Owner Domain Administration - 2026-09-12](Documentation/Change%20Records/Owner%20Domain%20Administration%20-%202026-09-12.md): `DK-user` in all three tiers and WAC over WinRM HTTPS.
- [ObiPC Workstation Join - 2026-09-11](Documentation/Change%20Records/ObiPC%20Workstation%20Join%20-%202026-09-11.md)
- [Owner Account Workstation Admin - 2026-09-11](Documentation/Change%20Records/Owner%20Account%20Workstation%20Admin%20-%202026-09-11.md)
- [Owner Account Soft Match - 2026-09-10](Documentation/Change%20Records/Owner%20Account%20Soft%20Match%20-%202026-09-10.md)
- [Shared Test Password and Admin Policy Relaxation - 2026-09-10](Documentation/Change%20Records/Shared%20Test%20Password%20and%20Admin%20Policy%20Relaxation%20-%202026-09-10.md)
- [Cloud Sync Configuration and First Cycle - 2026-09-10](Documentation/Change%20Records/Cloud%20Sync%20Configuration%20and%20First%20Cycle%20-%202026-09-10.md)
- [Entra Provisioning Agent Install - 2026-09-10](Documentation/Change%20Records/Entra%20Provisioning%20Agent%20Install%20-%202026-09-10.md)
- [Hybrid Identity Preparation - 2026-09-10](Documentation/Change%20Records/Hybrid%20Identity%20Preparation%20-%202026-09-10.md)
- [HQ-WS001 Workstation Join - 2026-09-10](Documentation/Change%20Records/HQ-WS001%20Workstation%20Join%20-%202026-09-10.md)
- [Forest Build - 2026-09-09](Documentation/Change%20Records/Forest%20Build%20-%202026-09-09.md)

## Related

- [Windows Admin Center deployment - 2026-09-12](../Windows%20Admin%20Center/Documentation/Change%20Records/Deployment%20-%202026-09-12.md)
- [Microsoft Intune](../Microsoft%20Intune/README.md), device management in the same tenant
- [Active Directory guide](../../Guides/Active-Directory.md)
- [Identity NTP and Client DNS - 2026-09-09](../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09.md)
- [Galaxy VMs](../../Operations/Inventory/Galaxy/VMs.md) for VMs 300 through 303 and VM 310
