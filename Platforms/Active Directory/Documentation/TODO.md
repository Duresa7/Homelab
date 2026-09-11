# Active Directory TODO

**Created:** 2026-09-11  
**Last updated:** 2026-09-11

I keep the detailed list for my Active Directory and hybrid identity platform here. The root TODO.md links here for the steps and completion checks.

## Windows Admin Center on HQ-MGT01 (decided 2026-09-11, not started)

1. I will install Windows Admin Center on HQ-MGT01 (192.168.65.12, VLAN 65) in gateway mode over SSH, using a self-signed certificate at first. I want one browser console for day-to-day management instead of the VM consoles. This step is done when the gateway service runs and listens on TCP 443.
2. I will create a UniFi firewall policy allowing Secure Client (VLAN 60) to HQ-MGT01 on TCP 443 for browser access. This step is done when I can open the gateway from ObiPC.
3. I will create a second UniFi firewall policy allowing HQ-MGT01 to Secure Client on TCP 5985/5986 for WinRM to workstations. The controllers share HQ-MGT01's VLAN, so they need no inter-VLAN rule. This step is done when WinRM from HQ-MGT01 reaches ObiPC.
4. I will register HQ-DC01, HQ-DC02, HQ-MGT01, ObiPC, and HQ-WS001 as connections and enable the Active Directory and DNS extensions. This step is done when all five connections open and both extensions are available.
5. I will sign in with DK-t0 for controller work and DK-user for workstation work. The initial setup is done when I manage a user, a DNS record, and a workstation service from the browser on ObiPC and verify each change on its target.
6. I will replace the self-signed certificate with a proper certificate later. This follow-up is done when the gateway presents a valid certificate for its browser address and ObiPC trusts its issuer without a certificate warning.

## RSAT on ObiPC (decided 2026-09-11, not started)

1. I will install the optional features `Rsat.ActiveDirectory.DS-LDS.Tools`, `Rsat.GroupPolicy.Management.Tools`, `Rsat.Dns.Tools`, and `Rsat.ServerManager.Tools` on ObiPC over SSH. This step is done when each capability shows `Installed` in `Get-WindowsCapability -Online`.
2. I will open the consoles with "Run as different user" as DK-t0 for changes. I need RSAT for Group Policy editing because Windows Admin Center has no policy editor. This work is done when Group Policy Management opens from ObiPC and shows the domain's five policies: `C-CMP-LAPS`, `C-SRV-LocalAdmins`, `C-WKS-LocalAdmins`, `Default Domain Policy`, and `Default Domain Controllers Policy`.

## Restore the temporary testing state

1. I will restore `PSO-Admins` `MinPasswordLength` to 20 as recorded in [Shared Test Password and Admin Policy Relaxation - 2026-09-10](Change%20Records/Shared%20Test%20Password%20and%20Admin%20Policy%20Relaxation%20-%202026-09-10.md). This step is done when the policy reads back as 20 on both controllers.
2. I will set unique passwords on IK-user, AH-user, DK-t0, and DK-t2 from their own vault items, with the admin passwords meeting the restored 20-character minimum. For each account I will verify that the stored password succeeds and a wrong-password control fails. For DK-t0 I will use a Kerberos interactive logon on a controller because Protected Users blocks the ordinary credential-validation method. This step is done when all four accounts pass both checks and their vault items match their directory passwords.
3. I will record the restored policy and the four validation results without password values. The domain default minimum of 8 is my accepted standing policy and is not restored. testuser has had its own password since 2026-09-10. This work is done when the record closes the four shared-password items and confirms the domain default remains 8.

## Credential validation failure auditing on both controllers

1. I will set the `Credential Validation` audit subcategory to `Success and Failure` on HQ-DC01 and HQ-DC02. Both currently audit Success only, so lockouts leave no 4776 failure trail.
2. I will run `auditpol /get /subcategory:"Credential Validation"` on each controller and record the results. This work is done when both read back `Success and Failure` and the change record includes both checks.

## BitLocker for physical workstations (baseline decision, open)

1. I will settle the physical workstation baseline as TPM-only BitLocker with recovery keys backed into Active Directory by policy. ObiPC's system drive is unencrypted, and the directory schema supports recovery-key storage. The decision is done when I record the baseline and its scope, `OU=Standard,OU=Workstations`.
2. I will configure and apply the recovery-key policy to that OU. This step is done when ObiPC's resultant policy requires recovery information to be stored in Active Directory before BitLocker is enabled.
3. I will enable BitLocker on ObiPC's system drive with TPM-only startup protection. This work is done when the drive reports fully encrypted with protection on and I verify that the matching recovery-key object exists beneath ObiPC's computer object in Active Directory.

## Cloud Sync device export timing (observation to settle)

1. I will use the next workstation to check scheduled export timing. Both existing workstations needed Provision on demand before their devices appeared in the tenant, but I watched the scheduled cycle for at most 14 minutes. After the next workstation is ready for hybrid join and in the device sync scope, I will record the start time and wait 30 minutes before using Provision on demand.
2. I will record whether the device appears during that window and how long it takes. If it is still absent after 30 minutes, I will provision it on demand and record that result. This observation is settled when the record states whether scheduled export succeeded or on-demand provisioning was needed, with elapsed times and the resulting tenant device state.

## Identity aliases in published records (policy change 2026-09-11)

1. I now use aliases for people in all published Active Directory and Microsoft 365 records, with the mapping kept in an unpublished file. Every new record uses IK-user, AH-user, DK-user, DK-t0, DK-t2, DK-admin, or BG-admin from the first draft; testuser stays as written. Each record is ready to publish when I have checked it against the mapping and found no real names or account names for people.
2. I rewrote the unpushed history before the first push. That cleanup is complete; I keep the alias check as part of every new record's publication check.

## Daily account elevation on ObiPC

1. After I sign out and sign back in as DK-user, I will observe my first elevation prompt on ObiPC following the 2026-09-11 group change. This check is done when I see a consent prompt (Yes/No) rather than a credential prompt.

## Done in this build, kept here for the record

1. 2026-09-09: I built the forest and verified replication, DNS, policy, LAPS, and external time.
2. 2026-09-10: I joined HQ-WS001 to the domain and verified its Microsoft Entra hybrid join.
3. 2026-09-10: I installed the Entra provisioning agent and configured Cloud Sync, with the first user export verified.
4. 2026-09-10: I soft-matched DK-user to the existing tenant account and moved its administrative roles to DK-admin.
5. 2026-09-11: I joined ObiPC to the domain, verified its Microsoft Entra hybrid join, and enabled Secure Boot.
6. 2026-09-11: I made DK-user a Tier 2 workstation administrator through `ADM-T2-WorkstationAdmins`.
