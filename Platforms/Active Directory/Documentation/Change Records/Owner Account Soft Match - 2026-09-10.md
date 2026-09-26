# Owner Account Soft Match

**Created:** 2026-09-10  
**Last updated:** 2026-09-25

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
| Object | `CN=DK-user,OU=Staff,OU=People,DC=ad,DC=alphasecunited,DC=com` |
| `sAMAccountName` | `DK-user` |
| `userPrincipalName` and `mail` | `DK-user@alphasecunited.com` |
| Given name, surname, display name | `<REDACTED_DISPLAY_NAME>`, matching the cloud object |
| Groups | `ROL-Staff` only. **Not** in `APP-EntraCloudSync-Users` yet, so Cloud Sync cannot see it. |
| Password | generated 24 characters at creation, set from standard input, never on a command line; replaced at 10:59 PM with the Microsoft 365 password already in use, see below |

Verified the same minute: `ValidateCredentials` True for the stored value and False for a one-character-off control; the account replicated to `HQ-DC02`.

The account stays outside the scope group until the cloud side is ready, because the first export is the only moment the match is evaluated. If the directory object reached the tenant while the cloud account still held a role, the tenant would create a quarantined duplicate that has to be hard-deleted before a second attempt.

## Sequence

1. Create the cloud-only administrator account, assign Global Administrator, register MFA, and prove it can sign in to the Entra admin center. `BG-admin` keeps Global Administrator throughout, so no step leaves the tenant without an administrator.
2. Remove every directory role from `DK-user@alphasecunited.com`.
3. Set the directory password to the value I want to use daily, from the vault item.
4. Add `DK-user` to `APP-EntraCloudSync-Users` and provision it on demand. The expected result is an update of the existing object, not a create, and the object id is unchanged.
5. Prove it: sign in to Microsoft 365 with the directory password, MFA still prompts, mailbox intact, and `DK-user` shows *On-premises sync enabled: Yes*. Sign in to `HQ-WS001` as `ALPHASEC\DK-user`.

## Progress

- **Step 1 done, 10:33 PM.** `DK-admin@alphasecunited.com`, display name `DK-admin`, created in the Microsoft 365 admin center with no licence. Global Administrator assigned as an active, direct assignment, confirmed on the account's Assigned roles page. Signed in, password changed, Microsoft Authenticator registered. Password stored in the account's own password manager item.
- **Step 3 decided.** The generated 24-character value in the directory account's vault item is the daily password; no reset needed.
- **Step 2 done, before 10:45 PM.** Every role removed from `DK-user@alphasecunited.com`; its Assigned roles page read *No directory roles assigned*, seen while signed in as the administrator account.
- **Step 4 done, 10:45 PM to 10:50 PM.** `DK-user` added to `APP-EntraCloudSync-Users` on `HQ-DC01` at 10:45:27 PM; `HQ-DC02` showed the membership within thirty seconds. Provision on demand for the distinguished name then passed all four stages: imported, in scope, **Successfully matched object**, and *User 'DK-user@alphasecunited.com' was updated in Microsoft Entra ID*. Updated, not created, is the whole point: the tenant took over the existing object rather than making a second one. The exported attributes were the directory values set earlier, display name `<REDACTED_DISPLAY_NAME>`, given name, common name, the description, and `AccountEnabled` True. The object id read from the account's own signed-in profile is the same before and after the match, which is the direct proof that mailbox, licence and MFA methods stayed with it.

- **Step 3 revisited, 10:59 PM.** The generated value was not what I wanted. I had meant to keep the password already in use for Microsoft 365, and I let the generated value through by mistake, so for a few minutes after the match the account signed in with a value I had never typed. Corrected by resetting the directory account from the password manager item that holds the Microsoft 365 password, via standard input: `RESET OK`, `PasswordLastSet` 10:59:17 PM on both controllers, `ValidateCredentials` True for the value and False for the one-character-off control. Hash sync then returns the tenant to the password already in use. The item created earlier for the generated value was archived, not deleted, and the daily password now lives only in the item that holds my Microsoft 365 password. Next time a generated placeholder is about to become someone's daily password, I confirm the intended value before the object is exported, because after the soft match the directory value is the one they type everywhere.
- **Noted, my decision.** The administrator account and the daily account deliberately hold the same password. That recouples what the split separated: a directory compromise yields the administrator password too, and MFA on the administrator account is the remaining barrier. Recorded so the choice is visible; it can be undone by changing either account's password on its own.

- **Step 5, tenant side, 11:04 PM.** The account's Overview page in the Entra admin center reads *On-premises sync enabled: Yes*, last sync 11:04 PM, on-premises distinguished name `CN=DK-user,OU=Staff,OU=People,DC=ad,DC=alphasecunited,DC=com`, on-premises SAM account name `DK-user`, on-premises domain `ad.alphasecunited.com`, and no provisioning errors. *Last password change* reads 10:59 PM, the minute of the directory reset, which is hash sync carrying the corrected password. Object id unchanged, created date still Jun 30, 2026, usage location still United States, account enabled, and the password policy now `DisablePasswordExpiration`, which the sync sets on every synced user so that tenant expiry never fights the directory. Sign-in sessions valid from 10:59 PM, so any session opened under the placeholder password is revoked.

One thing on that page predates the sync and needs a look: *Mail nickname* reads `AH-user`, not `DK-user`. The export carried no alias (the directory object has no `mailNickname`, and the export detail showed *Alias* blank), so this is the cloud object's original alias and probably the name the account was first created under on Jun 30, 2026. It matters only if `AH-user@alphasecunited.com` also appears among this account's proxy addresses, because then AH-user's mailbox, whose sign-in name is `AH-user@alphasecunited.com`, could not have taken that address as its primary. Check the account's *Proxy addresses* and AH-user's *Mail nickname*; if the address is on my object, remove it there and the alias corrects itself with AH-user's next licence change or with a mailbox alias edit in Exchange.

- **Step 5, Microsoft 365, before 11:12 PM.** Signed in to Microsoft 365 as `DK-user@alphasecunited.com` with the usual password and reached the mailbox. The Overview page at that point showed the account enabled, zero assigned roles, two licences, and a sign-in identifier of `userPrincipalName` issued by the tenant. AH-user's Overview page was checked alongside it: created 2:20 PM by the first sync cycle, one licence, sign-in identifier `AH-user@alphasecunited.com`.
- **Step 5, workstation, 11:14 PM.** Verified on `HQ-WS001` itself through the QEMU guest agent, with the password piped from the vault over standard input. The first attempt at 11:12 PM found VM 310 powered off mid-reboot; the second, using `Start-Process -Credential`, failed with *Access is denied* for both the right and the wrong password, because the guest agent runs in the system session where that call cannot create a process as another user, so it says nothing about the credential. The third used the Windows `LogonUser` API with the interactive logon type, which does work from that session and checks both the password and the right to log on locally to this machine: **INTERACTIVE LOGON OK** for the vault value, *Win32 error 1326, the user name or password is incorrect* for the one-character-off control. That is the workstation sign-in for `ALPHASEC\DK-user`, observed rather than assumed.

## Result

`DK-user@alphasecunited.com` is a directory-mastered account with its Business Premium seat, mailbox, MFA methods and object id intact, signing in with the same password as before the move. Its administrative roles live on the cloud-only `DK-admin@alphasecunited.com`, and `BG-admin` remains the break-glass account. The directory account is a standard user in `OU=Staff,OU=People`, member of `ROL-Staff` and `APP-EntraCloudSync-Users`, and holds no tiered admin membership.

## The mail nickname, checked

Both proxy address panels read at about 11:20 PM. My object carries one address, `SMTP:DK-user@alphasecunited.com`. AH-user's carries `SMTP:AH-user@alphasecunited.com` as primary and `smtp:AH-user@alphasecunit.onmicrosoft.com`, and his mail nickname is `AH-user`. So `AH-user@alphasecunited.com` belongs only to AH-user, mail for each address reaches the right mailbox, and the `AH-user` nickname on my object is a label with no address behind it. Cosmetic, left as is. If it ever needs tidying, the clean route now that the account is synced is to set `mailNickname` to `DK-user` on the directory object and let the next cycle export it as the alias, rather than editing the cloud side.

## Open

Nothing. Closed 11:20 PM on 2026-09-10.
