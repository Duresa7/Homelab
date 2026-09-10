# Shared Test Password and Admin Policy Relaxation

**Created:** 2026-09-10  
**Last updated:** 2026-09-10

On 2026-09-10 I set a shared password across five accounts for a testing window, at the owner's request, so that hybrid sign-in and Cloud Sync could be exercised with one simple credential. This is explicitly temporary. It weakened two controls, both recorded here so they can be restored.

## What changed

The shared value is held in the password manager item `ALPHASEC - Standard User Template`. It meets the default domain policy.

| Account | Tier | Result |
|---|---|---|
| `IK-user` | staff | Set to the template. Validated. |
| `AH-user` | staff | Set to the template. Validated. |
| `DK-t2` | Tier 2 admin | Set to the template. Validated. |
| `DK-t0` | Tier 0 admin | Set to the template. See the Protected Users note below. |
| `testuser` | staff | Could **not** take the template. See the constraint below. |

Each account's own password manager item was updated to match, so the vault stays truthful.

## Control 1: PSO-Admins lowered from 20 to 14

The three `ADM-` groups are covered by the fine-grained policy `PSO-Admins`, which required 20 characters. The template is shorter than that, so the two admin accounts could not take it under the existing policy. At the owner's direction I lowered `PSO-Admins` `MinPasswordLength` from 20 to 14. Every other attribute of the policy is unchanged, and it still applies to `ADM-T0-DomainAdmins`, `ADM-T1-ServerAdmins`, and `ADM-T2-WorkstationAdmins`.

**To restore:** set `PSO-Admins` `MinPasswordLength` back to 20 and reset both admin accounts to fresh 20-character values from their own vault items.

## Control 2: Tier 0 and Tier 2 admins share a password with standard users

`DK-t0` and `DK-t2` now hold the same password as three standard users. The tiered model exists precisely to keep admin credentials separate, so this is a deliberate, temporary regression for testing only. Rotate both admin accounts to unique values before this environment does anything real.

## The constraint I found: testuser cannot take this template

The `testuser` account rejected the template with *the password does not meet the length, complexity, or history requirement*. The cause is Windows password complexity, which forbids a password from containing the account's own name. The template value contains part of the account's own name, confirmed structurally without printing the value, so this one account is permanently unable to use it while complexity is enabled. The other four accounts, whose names do not appear in the value, took it without trouble.

Because `testuser` is the account chosen to prove the hybrid sign-in path, this matters. Until the template value is changed to one containing no account-name words, `testuser` holds a unique generated 16-character password instead, recorded in its own vault item with a note explaining why. The recommended fix is to set the template to a generic value with no names, after which all five accounts can share it.

## Two verification traps recorded

Both cost real time.

- **`DirectoryEntry.NativeObject` does not validate a password when run on a domain controller as an already-authenticated admin.** The bind reuses the existing security context and returns success for any password string, including a wrong one. A negative control, a deliberately wrong password, exposed it. Use `System.DirectoryServices.AccountManagement.PrincipalContext.ValidateCredentials` instead, and always run a wrong-password negative control.
- **`ValidateCredentials` returns False for a Protected Users member even with the correct password**, because the method it uses is one Protected Users blocks. Confirm the reset another way: `Set-ADAccountPassword -Reset` throws on a policy violation, and `pwdLastSet` updates to the reset time.

## Verification

Read back on 2026-09-10:

- `IK-user`, `AH-user`, `DK-t2`: `ValidateCredentials` returned True against the template value, after a wrong-password negative control returned False.
- `DK-t0`: `pwdLastSet` updated to the reset time and `Set-ADAccountPassword` raised no error; direct validation is blocked by Protected Users membership, which was confirmed.
- `testuser`: `ValidateCredentials` returned True against its unique generated password.
- `PSO-Admins` `MinPasswordLength` read back as 14, still applied to the three `ADM-` groups.
- Five password manager items confirmed present and consistent with the directory, values not revealed.

## Open

- Owner to decide whether to change the template value so `testuser` can join the shared password.
- Restore both controls before production: `PSO-Admins` back to 20, and unique passwords on the two admin accounts.
