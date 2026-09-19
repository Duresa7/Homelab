# Active Directory TODO

**Created:** 2026-09-11  
**Last updated:** 2026-09-19

I keep the detailed list for my Active Directory and hybrid identity platform here. The root TODO.md links here for the steps and completion checks.

## Windows Admin Center on HQ-MGT01 (deployed, browser management checks open)

I installed the gateway on 2026-09-11 and verified it on 2026-09-12. TCP 443 is listening, all five shared connections are saved, the Active Directory and DNS extensions are installed, and all five targets answer WinRM. Browser access covers all of VLAN 50 and VLAN 60, plus my MacBook Air M3 and Pixel on VLAN 10. I confirmed the sign-in page from a personal device and successful browser sign-in on 2026-09-12. The [deployment record](../../Windows%20Admin%20Center/Documentation/Change%20Records/Deployment%20-%202026-09-12.md) holds the firewall, DNS, authentication, and cleanup results.

I expanded DK-user to domain and server administration and verified gateway-session-only WAC connections and elevated Kerberos HTTPS sessions on all five targets on 2026-09-12. The [access change record](Change%20Records/Owner%20Domain%20Administration%20-%202026-09-12.md) contains the replicated memberships, gateway delegation, and final verification.

1. I will sign out of WAC and sign back in with my domain-qualified username, then use **Use my Windows account**. The authenticated API path is verified; I will still click through the tools I use in the browser. Existing Windows desktop sessions need sign-out and sign-in to pick up the new administrative groups locally.
2. I will manage a user, a DNS record, and a workstation service from the browser on ObiPC and verify each change on its target. These workflow exercises remain open; successful target queries and elevated tokens are already verified.
3. I will replace the browser self-signed certificate before it expires on 2026-11-10 at 10:54:56 PM EST. This follow-up is done when my client devices trust the replacement without a warning.
4. I will renew the five WinRM HTTPS certificates before 2027-09-12 and update HQ-MGT01's trust store and the target listener bindings. This is done when certificate validation and all five authenticated WAC queries pass again.
5. I will include WinRM HTTPS, gateway certificate trust, source-restricted TCP 5986 access, a saved connection, and delegation from HQ-MGT01 when onboarding future WAC targets. Existing administrative group policy covers machines in the server and workstation OUs; transport and delegation need per-target setup.

## RSAT on ObiPC (decided 2026-09-11, not started)

1. I will install the optional features `Rsat.ActiveDirectory.DS-LDS.Tools`, `Rsat.GroupPolicy.Management.Tools`, `Rsat.Dns.Tools`, and `Rsat.ServerManager.Tools` on ObiPC over SSH. This step is done when each capability shows `Installed` in `Get-WindowsCapability -Online`.
2. I will open the consoles with my regular DK-user account, which has domain administration rights since 2026-09-12. I need RSAT for Group Policy editing because Windows Admin Center has no policy editor. This work is done when Group Policy Management opens from ObiPC and shows the domain's five policies: `C-CMP-LAPS`, `C-SRV-LocalAdmins`, `C-WKS-LocalAdmins`, `Default Domain Policy`, and `Default Domain Controllers Policy`.

## Online workstation sign-in (applied 2026-09-19, interactive checks open)

I applied `C-WKS-OnlineLogon` to the Workstations OU and verified both clients and a disconnect/reconnect on `HQ-WS001`. The [change record](Change%20Records/Online%20Workstation%20Sign-In%20-%202026-09-19.md) distinguishes those checks from the remaining interactive tests.

1. With work saved, I will sign in using a domain password while connected, disconnect the network, lock, and confirm that offline unlock is rejected. I will then reconnect and confirm that the same password unlocks the session. Done when both outcomes are observed on each workstation.
2. I will confirm a fresh offline domain sign-in is rejected and the PIN, face, fingerprint, picture-password, and FIDO sign-in tiles are unavailable. I will verify the next foreground startup/sign-in policy cycle. Done when the sign-in screen agrees with the applied registry settings and reconnecting restores domain sign-in.
3. During the ObiPC restricted-account walkthrough, I will disconnect the network and verify the existing application and Settings restrictions still hold. Done when the offline behavior and relevant AppLocker events are recorded. The Script collection is still audit-only; the sign-in policy does not change that.

## Restore the temporary testing state

On 2026-09-12 I required IK-user and AH-user to change their passwords at next domain logon and verified the flag on both controllers. Their own password changes are pending and supersede the administrator-set staff passwords proposed below. See [Staff First Login Password Change](Change%20Records/Staff%20First%20Login%20Password%20Change%20-%202026-09-12.md).

1. I will restore `PSO-Admins` `MinPasswordLength` to 20 as recorded in [Shared Test Password and Admin Policy Relaxation - 2026-09-10](Change%20Records/Shared%20Test%20Password%20and%20Admin%20Policy%20Relaxation%20-%202026-09-10.md). This step is done when the policy reads back as 20 on both controllers.
2. I will set unique passwords on IK-user, AH-user, DK-t0, and DK-t2 from their own vault items, with the admin passwords meeting the restored 20-character minimum. For each account I will verify that the stored password succeeds and a wrong-password control fails. For DK-t0 I will use a Kerberos interactive logon on a controller because Protected Users blocks the ordinary credential-validation method. This step is done when all four accounts pass both checks and their vault items match their directory passwords.
3. I will record the restored policy and the four validation results without password values. The domain default minimum of 8 is my accepted standing policy and is not restored. testuser has had its own password since 2026-09-10. This work is done when the record closes the four shared-password items and confirms the domain default remains 8.

## Credential validation failure auditing on both controllers

1. I will set the `Credential Validation` audit subcategory to `Success and Failure` on HQ-DC01 and HQ-DC02. Both currently audit Success only, so lockouts leave no 4776 failure trail.
2. I will run `auditpol /get /subcategory:"Credential Validation"` on each controller and record the results. This work is done when both read back `Success and Failure` and the change record includes both checks.

## ObiPC lockdown follow-ups (applied 2026-09-18, user side unobserved)

The [lockdown record](Change%20Records/ObiPC%20Recovery%20and%20Settings%20Lockdown%20-%202026-09-18.md) and the [incident](../../../Security/Incidents/Active%20Directory/ObiPC%20Wiped%20from%20the%20Recovery%20Menu%20-%202026-09-18.md) hold the detail.

1. After `IK-user`'s first sign-in since the rebuild, I will read `gpresult /user` for his session and the AppLocker 8004 events from his first day, and confirm the Settings `showonly:` list, the Control Panel allowlist, `NoClose` and the MMC restriction are in effect and that nothing he needs was denied. Done when each is observed on his session and any needed page or path is added.
2. I will watch what Shift+Restart and `shutdown /r /o` present with the recovery environment unmapped, from a session of my own. Done when the observed menu is recorded and nothing in it launches a reset.
3. During his first week I will read the AppLocker 8004 events for anything the closed developer carve-out blocks that he legitimately needs, and answer each with an Action1 deployment or a publisher rule, never by reopening a user-writable path. Done when a week passes with every 8004 either deployed or declined in writing.
4. After a week of Script-collection 8003 audit events, I will add whatever paths the log shows and switch that collection to enforced; then a separate audit for `msiexec.exe` before denying it; `rundll32.exe` only as its own change with a test pass. Done when each is enforced with a readback.
5. I will narrow the Appx allow to Microsoft publishers after inventorying installed packages, as a standalone change verified against Start, Search, Settings, Photos, Terminal and Notepad. The Microsoft Store, the Store purchase app and the Xbox app are already denied for the restricted group as of 2026-09-19; this step is about the remaining broad `Everyone` allow.
6. I will confirm on `IK-user`'s next sign-in that the Store denies take effect, by looking for event 8022 in `Microsoft-Windows-AppLocker/Packaged app-Execution`, and that Store-delivered updates for his existing apps still arrive. This step is done when a blocked Store launch is in the log and no app update has stalled.
7. I will sign in to `ObiPC` as `testuser`, which I moved into `ROL-ObiPC-Restricted` on 2026-09-19, and walk the restricted experience end to end: the Store, the Store purchase app and the Xbox app, then the Settings allowlist, the power menu, Control Panel and an executable in the profile. Done when a blocked Store launch appears as event 8022 in `Microsoft-Windows-AppLocker/Packaged app-Execution` after 2026-09-19 10:23:35 and each user-side control is observed.
8. When that walkthrough is finished I will move `testuser` back to `ROL-ObiPC-Unrestricted`. The membership is a test fixture, and leaving it in place puts a restricted-group SID on a shared account. Done when the two groups read two and three members again and the change record says so.
9. After every Windows feature update I will confirm `recovery.log` shows the task turning the recovery environment back off. Done when the log line for that boot reads `WinRE=Disabled`.

## BitLocker for physical workstations (baseline decision, open)

1. I will settle the physical workstation baseline as BitLocker with **TPM+PIN** and recovery keys backed into Active Directory by policy. I had planned TPM-only; the 2026-09-18 wipe changed that, because Microsoft lists only TPM+PIN and password protectors as forcing the recovery key before a "Remove everything" reset from the recovery environment, so TPM-only would not have stopped it. ObiPC's system drive is unencrypted, and the directory schema supports recovery-key storage. The decision is done when I record the baseline and its scope, `OU=Standard,OU=Workstations`.
2. I will configure and apply the recovery-key policy to that OU. This step is done when ObiPC's resultant policy requires recovery information to be stored in Active Directory before BitLocker is enabled.
3. I will enable BitLocker on ObiPC's system drive with TPM+PIN startup protection. This work is done when the drive reports fully encrypted with protection on and I verify that the matching recovery-key object exists beneath ObiPC's computer object in Active Directory.

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
7. 2026-09-12: I verified the Windows Admin Center deployment, five shared connections, AD/DNS extensions, network access, browser sign-in, and setup-file cleanup; target connection verification was completed in the access change below.
8. 2026-09-12: I added DK-user to domain and server administration, configured HQ-MGT01 delegation and WinRM HTTPS on five targets, verified all five WAC connections and elevated sessions, and removed the test credentials.
