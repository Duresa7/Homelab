# HQ-MGT01 Connection Credentials

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

## Symptom

After successful browser sign-in as DK-user, I selected the personal `hq-mgt01 [Gateway]` connection. The credentials pane had **Use my Windows account for this connection** selected and displayed `Your credentials didn't work` followed by `try again`.

## Checks and findings

I read the directory and HQ-MGT01 local groups through SSH Manager on 2026-09-12. DK-user is enabled and not locked out. Its authorization groups include `ADM-T2-WorkstationAdmins`, but not `ADM-T1-ServerAdmins`, `ADM-T0-DomainAdmins`, or `Domain Admins`. I identified this account internally as the unique member shared by `ROL-Staff` and `ADM-T2-WorkstationAdmins` and returned only its alias and role booleans.

HQ-MGT01's local Administrators group includes `ALPHASEC\ADM-T1-ServerAdmins` and `ALPHASEC\Domain Admins`. It has zero direct domain-user members; `ADM-T1-ServerAdmins` has zero members. The local `Administrator` account is enabled. None of the three Windows Admin Center target RBAC groups exists on HQ-MGT01. These checks establish that DK-user lacks the server administrative access expected by this connection. Workstation administrator membership does not grant it.

HQ-MGT01 also has zero `PrincipalsAllowedToDelegateToAccount` entries. Recent 4625 records included status `0xc000006d`, with substatus `0xc0000064` on type 8 logons and earlier `0xc000006a` failures. I did not correlate those records to this specific connection attempt, so they do not establish that its password was wrong.

All three resumed read commands exited zero. I retained no separate command transcript or published screenshot for these checks. The supplied screenshot establishes the interactive symptom; I did not reproduce the same request with the browser session credentials or test a corrected connection.

## Original connection workaround

For HQ-MGT01, I will select **Use another account for this connection** and use `HQ-MGT01\Administrator` with its current LAPS-managed password. The older stored local administrator password is stale, as established during deployment. I will leave **Use these credentials for all connections** unchecked because this account belongs to HQ-MGT01.

Browser gateway access and target-machine permissions are separate, as described in [Microsoft's access guidance](https://learn.microsoft.com/en-us/windows-server/manage/windows-admin-center/configure/user-access-control). I made no account, group, delegation, or service changes during this diagnosis. At that point, the explicit administrator connection and target management checks remained open; the later resolution below supersedes that workaround.

## Resolution

Later on 2026-09-12 I chose to grant DK-user domain and server administration. I added it to the existing Tier 0 and Tier 1 groups, configured HQ-MGT01 delegation on all five targets, and switched WAC to trusted WinRM HTTPS after identifying a separate IPS block affecting ObiPC over HTTP. All five WAC operating-system queries now return HTTP 200 using DK-user's gateway session only, and all five fresh Kerberos HTTPS sessions report an elevated administrator token. Gateway administrator settings also return HTTP 200. The [access change record](../../../Active%20Directory/Documentation/Change%20Records/Owner%20Domain%20Administration%20-%202026-09-12.md) contains the verification. Switching to the local Administrator account is no longer required for this workflow; I need a fresh WAC sign-in to replace the old session.
