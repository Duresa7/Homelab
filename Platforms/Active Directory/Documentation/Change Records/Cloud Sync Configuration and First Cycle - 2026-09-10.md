# Cloud Sync Configuration and First Cycle

**Created:** 2026-09-10  
**Last updated:** 2026-09-10

I created the AD to Microsoft Entra ID configuration in Entra Cloud Sync on 2026-09-10 and its first cycle created the three staff accounts and their scope group in the tenant. The portal work was done under `DK-user@alphasecunited.com` from my own workstation. Verification came from the tenant's provisioning and audit log exports, cross-checked against object identifiers read from `HQ-DC01`.

## Configuration

| Setting | Value |
|---|---|
| Configuration | `ad.alphasecunited.com`, AD to Microsoft Entra ID |
| Created | 2:10 PM |
| Password hash sync | Enabled |
| Device sync | Disabled at this point; next step |
| Exchange hybrid writeback | Disabled |
| Scope | Selected security groups: `CN=APP-EntraCloudSync-Users,OU=Applications,OU=Groups,DC=ad,DC=alphasecunited,DC=com`, saved 2:11:54 PM |
| Attribute mapping | Default |
| Prevent accidental deletion | Enabled, threshold 500 |
| Status after enabling | Healthy |

The tenant audit log records the sequence: the synchronization service principal added and the `DirSyncEnabled` flag set at 2:09:59 PM, the configuration added at 2:10:06 PM with password hash sync enabled, and the scope saved at 2:11:54 PM. Group scoping is what the portal itself describes as a pilot arrangement, with a warning that nested membership beyond the first level is not followed. That suits three direct members.

## First cycle

The scheduler ran without any provisioning on demand. The audit export shows the iteration starting at 2:19:54 PM, three user imports of type Add, and *Finished synchronizing all pending changes* at 2:19:59 PM. The provisioning log then records eight rows at 2:20:03 PM and 2:20:05 PM, all `Success`:

| Object | Action | Directory GUID | Tenant object |
|---|---|---|---|
| `APP-EntraCloudSync-Users` | Create, then Update | `72747174-78d6-4299-b7e5-7e3d72214b98` | `8e932c57-0faf-4f29-8381-14fac29cd0e6` |
| Test User, `testuser@alphasecunited.com` | Create, then Update | `<REDACTED_OBJECT_ID>` | `<REDACTED_OBJECT_ID>` |
| AH-user, `AH-user@alphasecunited.com` | Create, then Update | `<REDACTED_OBJECT_ID>` | `<REDACTED_OBJECT_ID>` |
| IK-user, `IK-user@alphasecunited.com` | Create, then Update | `<REDACTED_OBJECT_ID>` | `<REDACTED_OBJECT_ID>` |

Each row passed the three steps the log records: import from Active Directory, scope evaluation against the group filter, and export to Microsoft Entra ID. The provisioning log shows the group only by its GUID; I resolved it on `HQ-DC01` with `Get-ADObject -Filter 'objectGUID -eq ...'`, which returned `APP-EntraCloudSync-Users` with three members. The three user GUIDs match `Get-ADUser` on the same controller. The scope group syncing alongside its members is expected: a group used as a scoping filter is itself in scope.

The users kept their `alphasecunited.com` sign-in names because that suffix is verified on the tenant. Neither `DK-t0` nor `DK-t2` appeared, which is the intended result of scoping by group rather than by organisational unit.

On the directory side nothing changed. `msDS-ExternalDirectoryObjectId` is empty on all three users because Exchange hybrid writeback is off, and Cloud Sync writes nothing else back. The agent's service account logged on to `HQ-DC02` in bursts throughout, read from the controller's security log, which is the only trace the cycle leaves on premises.

## Password hash sync and the shared password

Password hash sync is on, so the tenant now holds a derived hash for each of the three accounts. `testuser` currently carries the domain `Administrator` password, set at my request for the testing window and recorded in [Shared Test Password and Admin Policy Relaxation](Shared%20Test%20Password%20and%20Admin%20Policy%20Relaxation%20-%202026-09-10.md). That record's restore list now has more weight behind it: a derivative of the break-glass domain password is in the cloud for as long as `testuser` keeps it, and any cloud sign-in as `testuser` types that password into a browser. Giving `testuser` its own password before real use is the first restore item, not the last.

The first sign-in test, `testuser` at a Microsoft 365 sign-in page with its directory password, is the proof that the hash reached the tenant. It has not been run yet.

## Open

1. Enable device sync in the configuration's properties, then provision `HQ-WS001` on demand and confirm it reports as hybrid joined.
2. Assign Business Basic to `IK-user`, `AH-user` and `testuser` in the Microsoft 365 admin center.
3. Sign in as `testuser` to Microsoft 365 with the directory password to prove password hash sync end to end.
4. Give `testuser` a unique password once the sign-in proof is done.
