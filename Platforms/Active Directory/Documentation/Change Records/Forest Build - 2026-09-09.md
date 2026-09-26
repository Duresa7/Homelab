# Forest Build

**Created:** 2026-09-09  
**Last updated:** 2026-09-10

I built the `ad.alphasecunited.com` forest on 2026-09-09 from the Windows Server 2025 template I prepared the day before. This record covers the promotion of both domain controllers, the directory structure, Group Policy, Windows LAPS, and the member server, along with the four problems that cost real time and how each one resolved.

## What I built

Three guests on `grey-server`, all on IDENTITY-A, VLAN 65, cloned from VM 300 `ws2025-template`.

| VM | Name | Address | Role |
|---|---|---|---|
| 301 | `HQ-DC01` | `192.168.65.10` | First domain controller, all five operations master roles, global catalog |
| 302 | `HQ-DC02` | `192.168.65.11` | Second domain controller, global catalog |
| 303 | `HQ-MGT01` | `192.168.65.12` | Member server for management tooling |

The forest and domain are `ad.alphasecunited.com` with NetBIOS `ALPHASEC`, both at the `Windows2016` functional level. I added `alphasecunited.com` as a UPN suffix and enabled the AD Recycle Bin.

## Promotion

`Install-ADDSForest` runs against the local controller only, so it does not hit the double-hop problem described below. I still ran it as a scheduled task under `NT AUTHORITY\SYSTEM` rather than over SSH, because the promotion restarts services the session depends on. The DSRM password was piped in on standard input from the password manager and the temporary file holding it was deleted in the same script, so it never appeared in an argument list or a log.

I renamed `Default-First-Site-Name` to `HQ` and mapped three subnets to it: `192.168.65.0/24`, `192.168.50.0/24`, and `192.168.60.0/24`. The client subnets are mapped now so that workstations joining later pick the right site from the first lookup.

DNS came up AD-integrated on both controllers: `ad.alphasecunited.com` at domain scope, `_msdcs.ad.alphasecunited.com` and `65.168.192.in-addr.arpa` at forest scope, all primary with secure dynamic update only. The forwarder is the gateway at `192.168.65.1` and scavenging is on with a 7-day no-refresh and 7-day refresh interval. External resolution answered from both controllers.

## The blank Administrator password

This is the one that would have been expensive to find later. Before promotion the local `Administrator` account on `HQ-DC01` had no password and carried the "password not required" flag. `Install-ADDSForest` promotes that account into the domain `Administrator`, so the forest would have been created with a passwordless built-in administrator, and the password manager entry I had already written for it would have described a credential that did not exist.

I caught it before promoting. The fix set a real password and cleared the flag:

```powershell
$p = [Console]::In.ReadLine()
$s = ConvertTo-SecureString $p -AsPlainText -Force
Set-LocalUser -Name Administrator -Password $s -PasswordNeverExpires $true
net user Administrator /passwordreq:yes | Out-Null
```

The value arrives on standard input rather than as a parameter. Anything passed as an argument to `qm guest exec` lands in the Proxmox task log.

## Replication looked broken and was not

`dcdiag /test:replications` returned `DsBindWithSpnEx() failed with error 5, Access is denied` on both controllers, and `repadmin /syncall` returned `SyncAll exited with fatal Win32 error: 8440`. Both looked like a broken forest an hour after building it.

They were not. An OpenSSH network logon gets no delegatable Kerberos ticket, so any check that binds to the *other* controller fails as the logged-on user. This is the classic double-hop. Commands that touch only the controller you are logged into work normally, which is why promotion, DNS configuration, and object creation all succeeded while the replication tests failed.

I proved replication with an object rather than a test. A contact created on `HQ-DC01` appeared on `HQ-DC02` in 4 seconds. Re-running the same checks in machine-account context through `qm guest exec`, which executes as `NT AUTHORITY\SYSTEM` and therefore as the computer account, returned 0 of 5 failures in both directions with `showrepl_errors=none`. The clock offset between the two controllers was 11 milliseconds, which ruled out time skew as a cause.

## HQ-MGT01 applied no Group Policy

After joining the domain, `HQ-MGT01` applied zero policies, including the Default Domain Policy, and its Group Policy log recorded the computer as `WORKGROUP\HQ-MGT01`. The controller side was correct: the computer object was in the right organisational unit, the secure channel was healthy, SYSVOL and the `NETLOGON` share were serving, and Kerberos worked.

The cause was that the machine was still running with its pre-join identity. A clean reboot after the join and a time resync fixed it, and the server then applied all three custom policies. Windows Time on that host had never synchronised, which I corrected with `w32tm /config /syncfromflags:domhier`.

## LAPS

I extended the schema with `Update-LapsADSchema` and granted computer self-write with `Set-LapsADComputerSelfPermission` on the `Servers`, `Workstations`, and `Staging` computer containers. `C-CMP-LAPS` backs passwords to Active Directory with 20 characters, a 30-day rotation, encryption, and a post-authentication reset, linked to `Servers` and `Workstations`.

One detail cost time: `Get-LapsADSchema` does not exist. Verify the extension by looking for the attribute instead.

```powershell
Get-ADObject -SearchBase (Get-ADRootDSE).schemaNamingContext -LDAPFilter '(lDAPDisplayName=msLAPS-EncryptedPassword)'
```

`HQ-MGT01` is LAPS-managed and holds a stored password expiring 2026-10-09.

## Verification

Read back from `HQ-DC01` on 2026-09-09 and again on 2026-09-10 after the time change:

- Replication 0 of 5 failures in both directions, no errors, confirmed in machine-account context.
- Both controllers are global catalogs in site `HQ`; all five operations master roles are on `HQ-DC01`.
- Thirty-one organisational units; computer and user redirection both point at `Staging`.
- Group Policy: `C-CMP-LAPS`, `C-SRV-LocalAdmins`, `C-WKS-LocalAdmins`, all settings enabled and linked as intended.
- `ALPHASEC\ADM-T1-ServerAdmins` is in the local `Administrators` group on `HQ-MGT01`.
- Default password policy at 14 characters with no expiry; `PSO-Admins` at 20 characters over the three `ADM-` groups.
- The residual `dcdiag` failures are a DFS Replication event and a system-log event, both reacting to a one-time `sshd` crash and a Secure Boot certificate advisory. Neither involves directory health.

## Open

- ~~Entra Cloud Sync is not installed; the agent needs an interactive Global Admin sign-in.~~ Done 2026-09-10; see [Entra Provisioning Agent Install - 2026-09-10](Entra%20Provisioning%20Agent%20Install%20-%202026-09-10.md).
- ~~`HQ-WS001`, the Windows 11 client that would prove the Tier 2 policy and LAPS reach a workstation, is not built.~~ Done 2026-09-10; see [HQ-WS001 Workstation Join - 2026-09-10](HQ-WS001%20Workstation%20Join%20-%202026-09-10.md).

## Evidence

The build ran through a shell on each server. The verification output is in the Verification section above; the [evidence folder](../../Evidence/Forest%20Build%20-%202026-09-09/Evidence-Index.md) holds no screenshots.
