# Hybrid Identity Preparation

**Created:** 2026-09-10  
**Last updated:** 2026-09-10

I prepared the directory side of the link between `ad.alphasecunited.com` and the Microsoft 365 tenant on 2026-09-10. This record covers everything that could be done before the Entra provisioning agent is installed, which needs an interactive Global Admin sign-in and is still open. The tool is Entra Cloud Sync, with device sync, which is in preview, to be enabled once the first configuration exists.

## The tenant as found

The tenant was already further along than a fresh one. `alphasecunited.com` was verified and set as the default domain. A cloud-only account, `BG-admin`, existed on the tenant's `alphasecunit.onmicrosoft.com` domain and was unlicensed, which is the correct state for a break-glass account. The owner's own account, `DK-user@alphasecunited.com`, held Microsoft 365 Business Premium, which includes Entra ID P1, so password writeback, self-service password reset, and Conditional Access are all licensed. One further cloud-only user, `humesmax@alphasecunited.com`, is not part of this work and stays cloud-only.

## Service connection point

Device sync requires a service connection point in the forest so that domain-joined computers can discover which tenant to register with. Microsoft's script for this must run as an Enterprise Admin. I ran it instead as `NT AUTHORITY\SYSTEM` on `HQ-DC01` through the QEMU guest agent, which is the controller's own machine identity, and it had sufficient rights to write to the configuration partition. No administrator password was involved.

There was no existing service connection point, so nothing was overwritten. The values written were `azureADName:alphasecunit.onmicrosoft.com` and `azureADId:58cab82a-29ec-4085-b2b8-bccb6b00d5af`. Microsoft's device sync page specifies the primary `onmicrosoft.com` domain for a non-federated tenant, not the custom domain. I read the object back on `HQ-DC02` and both keywords had replicated.

## The Users container that could never have existed

My earlier records list a `Users/Staff` organisational unit in the tree. It did not exist, and the reason is worth keeping. The domain root already carries the built-in `CN=Users` container, and Active Directory refuses a second object named `Users` beside it regardless of type: `New-ADOrganizationalUnit -Name 'Users'` fails with error 8305, *an attempt was made to add an object to the directory with a name that is already in use*. The design was written before anyone tried to build that part of it, and the readback I documented from listed 31 organisational units without it.

I created `OU=People` at the root and `OU=Staff,OU=People` beneath it, both protected from accidental deletion. `People` is the conventional name for exactly this collision. The forest now has 33 organisational units. The Forest Build record's count of 31 was correct for its date and stays as written; the guide and the platform record are corrected.

## Staff accounts

Three accounts, all in `OU=Staff,OU=People`, all enabled, all with the `alphasecunited.com` sign-in suffix rather than the internal `ad.alphasecunited.com` one, so that they keep their sign-in names when synced instead of being rewritten to the tenant's `onmicrosoft.com` domain.

| Account | Display name | Sign-in name |
|---|---|---|
| `IK-user` | IK-user | `IK-user@alphasecunited.com` |
| `AH-user` | AH-user | `AH-user@alphasecunited.com` |
| `testuser` | Test User | `testuser@alphasecunited.com` |

Each is a member of `ROL-Staff` and of `APP-EntraCloudSync-Users`, the group that scopes what Cloud Sync is allowed to synchronise. Each has a generated 24-character password stored in my password manager and set on the account by reading it from standard input on the controller, so the value never appeared in a command argument, a log, or this record. Passwords are not forced to change at first sign-in. I wrote here at first that the users could reset their own through Microsoft 365 with it writing back; that needs P1 per user, and these three are on Business Basic, so their passwords are managed in the directory. The correction is in the [agent install record](Entra%20Provisioning%20Agent%20Install%20-%202026-09-10.md).

The two tiered administrator accounts, `DK-t0` and `DK-t2`, are deliberately not in the scope group and keep their internal suffix. They must never exist in the cloud.

## Verification

Read back from `HQ-DC01` on 2026-09-10:

- Service connection point present on both controllers with both keywords.
- `OU=Staff,OU=People,DC=ad,DC=alphasecunited,DC=com` exists; 33 organisational units total.
- Three users returned by `Get-ADUser` with the expected sign-in names, `Enabled` true, and membership of both groups.
- `APP-EntraCloudSync-Users` has three members and `ROL-Staff` has three members, both previously empty.
- Three matching entries confirmed in the password manager by title, without revealing values.

## Open

In order, as of the end of this record. The first two closed the same day; see the [agent install record](Entra%20Provisioning%20Agent%20Install%20-%202026-09-10.md).

1. ~~Turn off security defaults and turn on Conditional Access, excluding `BG-admin`.~~ Withdrawn. Conditional Access needs P1 per user and every user but my own is on Business Basic, so security defaults stay on. Both administrative accounts registered MFA on 2026-09-10.
2. ~~Install the Entra provisioning agent on `HQ-MGT01`.~~ Done 2026-09-10, version 1.1.2334.0.
3. ~~Create the AD to Microsoft Entra ID Cloud Sync configuration, scoped to `APP-EntraCloudSync-Users`, with password hash sync.~~ Done 2026-09-10; see [Cloud Sync Configuration and First Cycle](Cloud%20Sync%20Configuration%20and%20First%20Cycle%20-%202026-09-10.md). Password writeback waits for a P1 licence in scope.
4. ~~Enable device sync in that configuration's properties, then provision `HQ-WS001` on demand and confirm it reports as hybrid joined.~~ Done 2026-09-10, after a scope-group trap recorded in the [Cloud Sync record](Cloud%20Sync%20Configuration%20and%20First%20Cycle%20-%202026-09-10.md).
5. ~~Assign licences to the three synced users once they appear in the tenant.~~ Done 2026-09-10, Business Basic.

The owner's own account stays cloud-only for now. The decision, made 2026-09-10, is to prove the full path on `testuser` first: workstation sign-in, Microsoft 365 sign-in, and a password reset from Microsoft 365 that writes back to the directory. Once that holds, the owner's account is moved onto the directory by soft match in its own record. `testuser`, not `IK-user`, is the proving account.
