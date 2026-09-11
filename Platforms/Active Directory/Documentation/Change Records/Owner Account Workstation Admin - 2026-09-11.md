# Owner Account Workstation Admin

**Created:** 2026-09-11  
**Last updated:** 2026-09-11

On 2026-09-11 I put my daily account, `DK-user`, into `ADM-T2-WorkstationAdmins`, so that it is a local administrator on every workstation through the existing `C-WKS-LocalAdmins` policy. The reason is plain: after the first day of using `ObiPC` I did not want a separate Tier 2 account for every elevation on my own machine.

## What I gave up, said once

The tiered model was built so that the account that reads mail is not an account with administrator rights. This change ends that on the workstation tier. If the daily account is ever phished, the attacker holds local administrator on every workstation rather than none. Tier 0 is untouched: `DK-t0` alone administers the controllers, and nothing on a workstation needs it. `DK-t2` stays in the group and keeps working; it is simply no longer needed on machines I sit at.

I chose this over the narrower option, a group placed into local Administrators on `ObiPC` alone by a policy filtered to that computer, because I wanted the right on every workstation, not one. The narrower option remains the way to give any future person admin on only their own machine.

## Change

`Add-ADGroupMember 'ADM-T2-WorkstationAdmins' -Members DK-user` on `HQ-DC01` at 10:43 AM. Read back:

| Check | Result |
|---|---|
| `ADM-T2-WorkstationAdmins` | `DK-t2`, `DK-user` |
| `DK-user` groups | `APP-EntraCloudSync-Users`, `ROL-Staff`, `ADM-T2-WorkstationAdmins` |
| Resultant password policy | `PSO-Admins`, no longer the domain default |
| `HQ-DC02` | membership replicated within twenty seconds |

## Two consequences of PSO-Admins applying

The fine-grained policy covers the three `ADM-` groups, so my daily account now falls under it.

- **Lockout tightens** from 10 attempts in 15 minutes to 5 attempts in 30 minutes. A mistyped password at the keyboard, in Outlook, and on the phone in quick succession is enough. Worth knowing before it happens.
- **The password now expires.** The domain default has no expiry, but `PSO-Admins` sets 365 days, so the directory will require a change around 2026-09-10 next year, counted from the last set at 10:59 PM on 2026-09-10. The tenant side does not fight it: synced users carry `DisablePasswordExpiration` in Entra, and the directory password is the only one. The current password is 17 characters, above the 14 the policy demands, so nothing had to change today.

`ADM-T2-WorkstationAdmins` is not in the Cloud Sync scope group, so this membership does not reach the tenant and grants nothing there.

## Taking effect

A Windows logon token is built at sign-in, so the right appears at my next sign-in to a workstation, not before. The test is that an elevation prompt on `ObiPC` asks for consent, Yes or No, instead of another account's credentials.

## Open

- First elevation on `ObiPC` under the daily account, to be observed after a sign-out and sign-in.
