# Active Directory

**Created:** 2026-09-09  
**Last updated:** 2026-09-10

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
| Workstation | `HQ-WS001` at `192.168.65.20` (VM 310), Windows 11 Pro 25H2, in `OU=Standard,OU=Workstations` |
| UPN suffix | `alphasecunited.com` added alongside the default |
| AD Recycle Bin | Enabled |
| DNS zones | `ad.alphasecunited.com` (domain scope), `_msdcs.ad.alphasecunited.com` (forest scope), `65.168.192.in-addr.arpa` (forest scope). All primary, AD-integrated, secure dynamic update only |
| DNS forwarder | `192.168.65.1` |
| Scavenging | Enabled, 7-day no-refresh and 7-day refresh |
| Default password policy | 14 characters, complexity on, history 24, no expiry, lockout 10 attempts for 15 minutes |
| Fine-grained policy | `PSO-Admins`, precedence 10, 20 characters, 365-day maximum age, lockout 5 attempts for 30 minutes |
| Time source | `HQ-DC01` synchronises from `time.cloudflare.com` at stratum 4; the other two follow the domain hierarchy |
| Remote access | `hq_dc01`, `hq_dc02`, and `hq_mgt01` in SSH Manager over OpenSSH on port 22, key only |

## Tiered Administration

The directory is laid out for a tiered administrative model. Tier 0 covers the forest itself, Tier 1 the member servers, and Tier 2 the workstations. Thirty-one organisational units carry that split, and both computer and user redirection point at `Staging` so a default-location join never lands an object in a container that no policy reaches.

| Group | Scope | Purpose | Members on 2026-09-09 |
|---|---|---|---|
| `ADM-T0-DomainAdmins` | Global | Nested into `Domain Admins` | `DK-t0` |
| `ADM-T1-ServerAdmins` | Global | Local administrator on member servers through Group Policy | none |
| `ADM-T2-WorkstationAdmins` | Global | Local administrator on workstations through Group Policy | `DK-t2` |
| `ROL-Staff` | Global | Role group for standard staff accounts | none |
| `APP-EntraCloudSync-Users` | Global | Scope group for Entra Cloud Sync | none |

`Domain Admins` holds the built-in `Administrator` account and `ADM-T0-DomainAdmins`, nothing else. `DK-t0` is in `Protected Users` and is flagged as sensitive and not delegated. The built-in `Administrator` is the break-glass account and is not used for daily work.

## Group Policy

| Policy | Status | Linked to |
|---|---|---|
| `C-CMP-LAPS` | All settings enabled | `Servers`, `Workstations` |
| `C-SRV-LocalAdmins` | All settings enabled | `Servers` |
| `C-WKS-LocalAdmins` | All settings enabled | `Workstations` |
| `Default Domain Policy` | All settings enabled | domain root |
| `Default Domain Controllers Policy` | All settings enabled | `Domain Controllers` |

The two local-administrator policies use Group Policy Preferences local users and groups. They replace the local `Administrators` membership with the matching tier group, so a server gets `ADM-T1-ServerAdmins` and a workstation gets `ADM-T2-WorkstationAdmins`. Both halves are proven on a live machine: `HQ-MGT01` carries the Tier 1 group and `HQ-WS001` carries the Tier 2 group, each placed there by policy rather than by hand.

## Windows LAPS

The schema is extended for Windows LAPS, confirmed by the presence of `msLAPS-EncryptedPassword`. Computers hold self-write permission on the `Servers`, `Workstations`, and `Staging` computer containers. `C-CMP-LAPS` backs passwords to Active Directory with 20 characters, a 30-day rotation, encryption on, and a post-authentication reset.

`HQ-MGT01` and `HQ-WS001` are both managed and hold stored passwords, expiring 2026-10-09 and 2026-10-10. Retrieve it with `Get-LapsADPassword -Identity HQ-MGT01 -AsPlainText`. The domain controllers are not LAPS-managed, which is expected: a domain controller has no local account database to manage.

## Credentials

Every account here is stored in my password manager. No password, DSRM password, or recovery key appears in this repository. Once a machine becomes LAPS-managed its stored local administrator password is authoritative and the password manager entry for that machine is stale.

## Open Items

- Entra Cloud Sync is not installed. The agent needs an interactive Global Admin sign-in to the tenant, so it is not something I can complete from a shell. `APP-EntraCloudSync-Users` is built and waiting.
- OpenSSH Server will not install on `HQ-WS001`. `Add-WindowsCapability` leaves the capability `NotPresent` and `Get-WindowsCapability -Online` hangs while the servicing stack is busy. Outbound HTTPS from that machine works, so it is not a network path problem. The workstation is therefore not in SSH Manager and is managed through the QEMU guest agent.
- `ADM-T1-ServerAdmins` and `ROL-Staff` are empty by design until there is a second administrator and real staff accounts.

## Records

- [Forest Build - 2026-09-09](Documentation/Change%20Records/Forest%20Build%20-%202026-09-09.md)
- [HQ-WS001 Workstation Join - 2026-09-10](Documentation/Change%20Records/HQ-WS001%20Workstation%20Join%20-%202026-09-10.md)
- [Active Directory guide](../../Guides/Active-Directory.md)
- [Identity NTP and Client DNS - 2026-09-09](../../Infrastructure/Network/UniFi/Documentation/Change%20Records/Identity%20NTP%20and%20Client%20DNS%20-%202026-09-09.md)
- [Galaxy VMs](../../Operations/Inventory/Galaxy/VMs.md) for VMs 300 through 303 and VM 310
