# Owner Account Soft Match

**Created:** 2026-09-10  
**Last updated:** 2026-09-10

This record moves my own Microsoft 365 account, `DK-user@alphasecunited.com`, from cloud-only onto the directory. The [Hybrid Identity Preparation](Hybrid%20Identity%20Preparation%20-%202026-09-10.md) record deferred this until the path was proven on `testuser`, which the [Cloud Sync record](Cloud%20Sync%20Configuration%20and%20First%20Cycle%20-%202026-09-10.md) closed on the afternoon of 2026-09-10.

## The constraint that changed the design

Microsoft Entra ID refuses to soft match an incoming directory user to a cloud account that holds an administrative role. The documented behaviour is that the incoming object is quarantined as a duplicate instead, and the documented workaround is to strip every role from the cloud account, let the match happen, and add the roles back. The same page says Microsoft strongly recommends against synchronising a directory account with a pre-existing administrative account at all, because once the account is synced, whoever controls the domain controllers holds the password of a tenant administrator, with MFA as the only remaining barrier.

My account held the tenant's administrative roles and was also meant to be the daily account for `HQ-WS001`. Those two uses cannot stay on one synced account without accepting that risk. The decision, made 2026-09-10 after both options were laid out, is the split Microsoft recommends:

| Account | Where mastered | Purpose | Licence |
|---|---|---|---|
| `DK-user@alphasecunited.com` | directory, after the soft match | daily work, mailbox, workstation sign-in | Business Premium, unchanged |
| new cloud-only administrator account | Entra ID only | admin centers; every directory role moves here | none needed |
| `BG-admin` | Entra ID only | break-glass, unchanged | none |

Directory roles are assigned independently of licensing, so the administrator account needs no seat. The one Premium feature that is per-user, Conditional Access, is not in use while security defaults are on; if it is turned on later, the administrator account is either licensed or excluded like the break-glass account. Business Premium stays on the same Entra object throughout, because a soft match changes where an account is mastered and which password it uses, not what it is licensed for.

## What a soft match does to the account

The match is evaluated on `userPrincipalName` and the primary SMTP address, both `DK-user@alphasecunited.com` on the cloud object, confirmed from the signed-in profile before anything was created. When the match succeeds the Entra object keeps its identity, mailbox, licence, MFA methods and passkey; every attribute with a value in the directory overwrites the cloud value; and password hash sync replaces the cloud password with the directory one. Attributes the directory leaves empty are not exported, so cloud-side values such as usage location survive.

## Directory account

Created 6:43 PM on `HQ-DC01`, mirroring the three staff accounts:

| Attribute | Value |
|---|---|
| Object | `CN=Duresa Kadi,OU=Staff,OU=People,DC=ad,DC=alphasecunited,DC=com` |
| `sAMAccountName` | `DK-user` |
| `userPrincipalName` and `mail` | `DK-user@alphasecunited.com` |
| Given name, surname, display name | Duresa, Kadi, Duresa Kadi, matching the cloud object |
| Groups | `ROL-Staff` only. **Not** in `APP-EntraCloudSync-Users` yet, so Cloud Sync cannot see it. |
| Password | generated 24 characters, stored in the account's own password manager item and set from standard input, never on a command line |

Verified the same minute: `ValidateCredentials` True for the stored value and False for a one-character-off control; the account replicated to `HQ-DC02`.

The account stays outside the scope group until the cloud side is ready, because the first export is the only moment the match is evaluated. If the directory object reached the tenant while the cloud account still held a role, the tenant would create a quarantined duplicate that has to be hard-deleted before a second attempt.

## Sequence

1. Create the cloud-only administrator account, assign Global Administrator, register MFA, and prove it can sign in to the Entra admin center. `BG-admin` keeps Global Administrator throughout, so no step leaves the tenant without an administrator.
2. Remove every directory role from `DK-user@alphasecunited.com`.
3. Set the directory password to the value I want to use daily, from the vault item.
4. Add `DK-user` to `APP-EntraCloudSync-Users` and provision it on demand. The expected result is an update of the existing object, not a create, and the object id is unchanged.
5. Prove it: sign in to Microsoft 365 with the directory password, MFA still prompts, mailbox intact, and `Duresa Kadi` shows *On-premises sync enabled: Yes*. Sign in to `HQ-WS001` as `ALPHASEC\DK-user`.

## Progress

- **Step 1 done, 10:33 PM.** `DK-admin@alphasecunited.com`, display name `DK-admin`, created in the Microsoft 365 admin center with no licence. Global Administrator assigned as an active, direct assignment, confirmed on the account's Assigned roles page. Signed in, password changed, Microsoft Authenticator registered. Password stored in the account's own password manager item.
- **Step 3 decided.** The generated 24-character value in the directory account's vault item is the daily password; no reset needed.

## Open

Steps 2, 4 and 5 above, in order, as of 10:35 PM on 2026-09-10. Step 2 gates step 4: the account does not enter the scope group until the roles are confirmed gone from `DK-user@alphasecunited.com`.
