# Staff First Login Password Change

**Created:** 2026-09-12  
**Last updated:** 2026-09-12

I required AH-user and IK-user to change their passwords at their next domain logon using `Set-ADUser -ChangePasswordAtLogon $true` on HQ-DC01. Each target resolved to exactly one directory account before the change. I did not reset either password.

Before the change, both accounts were enabled and neither required a password change. Both allowed password changes and had `PasswordNeverExpires` set to false.

The initial command applied both changes but returned exit code 1 during its combined verification. A separate read on HQ-DC01 confirmed both flags were set. I reapplied the AH-user flag successfully, then read both accounts directly from HQ-DC02. Both independent reads returned exit code 0 with empty stderr.

| Account | HQ-DC01 requires change | HQ-DC02 requires change | Enabled | Cannot change password | Password never expires |
|---|---|---|---|---|---|
| AH-user | True | True | True | False | False |
| IK-user | True | True | True | False | False |

I verified the requirement by testing `pwdLastSet -eq 0` on each controller. I retained no terminal transcript for these steps; the table records the observed readbacks.

The users' actual password changes remain pending their next domain logon. I did not test an interactive sign-in or verify the separate Microsoft 365 password-change prompt. This change does not close the shared-password cleanup until each user chooses a new password.
