# Shared Test Password and Admin Policy Relaxation

**Created:** 2026-09-10  
**Last updated:** 2026-09-11

On 2026-09-10 I set a shared password across four accounts, two standard users and two admin accounts, for a testing window so that hybrid sign-in and Cloud Sync could be exercised with one simple credential. This is explicitly temporary. It weakened two controls, both recorded here so they can be restored. I set `testuser` separately. Later the same day it left that arrangement and a third control was loosened to allow it; both are in the closing sections.

## What changed

The shared value is held in the password manager item `ALPHASEC - Standard User Template`. It meets the default domain policy.

| Account | Tier | Result |
|---|---|---|
| `IK-user` | staff | Set to the template. Validated. |
| `AH-user` | staff | Set to the template. Validated. |
| `DK-t2` | Tier 2 admin | Set to the template. Validated. |
| `DK-t0` | Tier 0 admin | Set to the template. See the Protected Users note below. |
| `testuser` | staff | Could **not** take the template. Set instead to the domain Administrator's password. See below. **Rotated to its own value at 5:13 PM the same day; see the closing section.** |

Each account's own password manager item was updated to match, so the vault stays truthful.

## Control 1: PSO-Admins lowered from 20 to 14

The three `ADM-` groups are covered by the fine-grained policy `PSO-Admins`, which required 20 characters. The template is shorter than that, so the two admin accounts could not take it under the existing policy. I lowered `PSO-Admins` `MinPasswordLength` from 20 to 14. Every other attribute of the policy is unchanged, and it still applies to `ADM-T0-DomainAdmins`, `ADM-T1-ServerAdmins`, and `ADM-T2-WorkstationAdmins`.

**To restore:** set `PSO-Admins` `MinPasswordLength` back to 20 and reset both admin accounts to fresh 20-character values from their own vault items.

## Control 2: Tier 0 and Tier 2 admins share a password with standard users

`DK-t0` and `DK-t2` now hold the same password as two standard users. The tiered model exists precisely to keep admin credentials separate, so this is a deliberate, temporary regression for testing only. Rotate both admin accounts to unique values before this environment does anything real.

## The constraint I found: testuser cannot take this template

The `testuser` account rejected the template with *the password does not meet the length, complexity, or history requirement*. The cause is Windows password complexity, which forbids a password from containing the account's own name. The template value contains part of the account's own name, confirmed structurally without printing the value, so this one account is permanently unable to use it while complexity is enabled. The other four accounts, whose names do not appear in the value, took it without trouble.

Because `testuser` is the account chosen to prove the hybrid sign-in path, this matters. I first gave it a unique generated password so the vault stayed truthful. I then chose a different route: `testuser` now carries the same password as the built-in domain `Administrator`, the break-glass account. That value is 19 characters, meets policy, and contains no part of the account name, so the directory accepted it. It is recorded in `testuser`'s own vault item with a note. This widens the exposure of the break-glass credential to a standard account and is part of the same temporary testing window; rotate it with the rest.

## Two verification traps recorded

Both cost real time.

- **`DirectoryEntry.NativeObject` does not validate a password when run on a domain controller as an already-authenticated admin.** The bind reuses the existing security context and returns success for any password string, including a wrong one. A negative control, a deliberately wrong password, exposed it. Use `System.DirectoryServices.AccountManagement.PrincipalContext.ValidateCredentials` instead, and always run a wrong-password negative control.
- **`ValidateCredentials` returns False for a Protected Users member even with the correct password**, because the method it uses is one Protected Users blocks. Confirm the reset another way: `Set-ADAccountPassword -Reset` throws on a policy violation, and `pwdLastSet` updates to the reset time.

## Verification

Read back on 2026-09-10:

- `IK-user`, `AH-user`, `DK-t2`: `ValidateCredentials` returned True against the template value, after a wrong-password negative control returned False.
- `DK-t0`: `pwdLastSet` updated to the reset time and `Set-ADAccountPassword` raised no error; direct validation is blocked by Protected Users membership, which was confirmed.
- `testuser`: `ValidateCredentials` returned True against the domain Administrator's password, after that same value was confirmed current against `Administrator` itself. `pwdLastSet` updated to the reset time.
- `PSO-Admins` `MinPasswordLength` read back as 14, still applied to the three `ADM-` groups.
- Five password manager items confirmed present and consistent with the directory, values not revealed.

## Control 3: default domain minimum password length lowered from 14 to 8

The hybrid sign-in proof completed on the afternoon of 2026-09-10, so `testuser` no longer needed the break-glass value. I chose its replacement and stored it in the password manager item `Microsoft - testuser`. The value has all four character classes and does not contain the account name, but it is 13 characters, and the domain default policy required 14. The first reset attempt at 4:54 PM was refused with *the password does not meet the length, complexity, or history requirement of the domain*, and `PasswordLastSet` did not move.

Rather than lengthen the value, I chose to lower the domain minimum to 8. At 5:12 PM I ran `Set-ADDefaultDomainPasswordPolicy -MinPasswordLength 8` against `HQ-DC01`, the PDC emulator. Every other setting is unchanged: complexity on, history 24, no expiry, minimum age one day, lockout 10 attempts for 15 minutes.

Unlike the other two controls, this one is not temporary. After the rotation I confirmed that 8 is the standing minimum for ordinary accounts, so the README records it as the policy and nothing here restores it. Two facts bound it. `PSO-Admins` has precedence over the domain default, so the tiered admin accounts still need 14. And Windows complexity stays on, so an 8-character value still needs three character classes and cannot contain the account name. Eight is the floor NIST SP 800-63B permits for a user-chosen password; the build chose 14 deliberately.

One thing to know before restoring this: the domain default lives in the `Default Domain Policy` GPO's security template, and a policy change made on the PDC emulator is written back into that GPO. The template read `MinimumPasswordLength = 14` before and `MinimumPasswordLength = 8` twenty seconds after, and the GPO version moved from 3 to 4 in both `GPT.ini` and the directory. A direct attribute change is therefore not undone at the next Group Policy refresh, and the same command restores it.

**If it is ever raised again:** `Set-ADDefaultDomainPasswordPolicy -MinPasswordLength <n>` on the PDC emulator, then confirm the template and GPO version followed. A password already set below the new minimum keeps working until it is next changed.

## testuser leaves the shared arrangement

With the minimum at 8 the reset succeeded at 5:13:13 PM. `testuser` now holds a value that is unique to it and is not derived from any other account. The domain item `ALPHASEC - testuser` was updated by piped JSON so the value never appeared on a command line, and its note now records the rotation; the two vault items agree, confirmed by comparing digests without printing either value. Password hash sync carried the change to the tenant, and I signed in to Microsoft 365 as `testuser@alphasecunited.com` with the new value shortly afterwards, which closes the loop from directory reset to tenant sign-in a second time.

Verification, all on 2026-09-10:

- `PasswordLastSet` moved from 10:41:23 AM to 5:13:13 PM on `HQ-DC01`, and `HQ-DC02` read the same value directly.
- `ValidateCredentials` returned True for the new value and False for the same value with one character appended, run in that order, and `badPwdCount` rose by one after the control.
- An interactive logon attempt on the controller with the new value failed with *the user has not been granted the requested logon type at this computer*, while the wrong-password control failed with *the user name or password is incorrect*. The different messages show the credential was accepted and only the logon right was refused, which is correct for a standard user on a domain controller.
- `Get-ADDefaultDomainPasswordPolicy` read 8 from both controllers.
- I left the four other accounts in the table above unchanged.

## Open

- Restore before production: `PSO-Admins` back to 20 and unique passwords on the two admin accounts. Control 3 is the accepted policy and stays.
- ~~A password on `testuser` that is not the break-glass value.~~ Done 5:13 PM on 2026-09-10.
