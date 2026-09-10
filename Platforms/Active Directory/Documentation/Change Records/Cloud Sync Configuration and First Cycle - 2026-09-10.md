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
| Device sync | Enabled later the same day; see below |
| Exchange hybrid writeback | Disabled |
| Scope | Selected security groups: `CN=APP-EntraCloudSync-Users,OU=Applications,OU=Groups,DC=ad,DC=alphasecunited,DC=com`, saved 2:11:54 PM; `CN=APP-EntraCloudSync-Devices,...` added after 2:58 PM |
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

The first sign-in test, `testuser` at a Microsoft 365 sign-in page with its directory password, is the proof that the hash reached the tenant. It passed later the same afternoon: `testuser` signed in at `office.com` with the directory password and registered the Authenticator app under security defaults. Business Basic was then assigned to `testuser`, `AH-user` and `IK-user` in the Microsoft 365 admin center. The Devices page lists `HQ-WS001` as *Microsoft Entra hybrid joined*, Windows `10.0.26200.6584`, registered 3:02 PM.

## Device sync and the hybrid join of HQ-WS001

Device sync, which is in preview, was enabled in the configuration's properties in the afternoon. Between 2:33 PM and 2:34 PM the configuration was deleted and recreated in the portal while that was being worked out; the audit log shows both configurations with password hash sync enabled and the scope saved again, and the users were re-imported as Add and matched to their existing tenant objects, so nothing in the tenant was disturbed. At 2:35 PM the workstation's distinguished name was pasted into the scoping filter by mistake and saved; it was removed a minute later and the filter read back as the single users group.

**The skip.** Provisioning `CN=HQ-WS001,OU=Standard,OU=Workstations` on demand as a device passed import, scope and match, then stopped at the fourth step: `Object was skipped`, `SkipReason = JoinNotFound`. Microsoft does not document that value. The change on the computer object that I made to give sync a delta, a `description`, made no difference. The workstation, meanwhile, was doing its part: its computer object had carried the self-signed registration certificate since 8:43 AM, its join task was in `fallback_sync` mode, and every attempt failed at the Device Registration Service with `0x801c03f3`, *The device object by the given id (41677d01-a299-4f17-8e29-675906799ac4) is not found*. The device was waiting for sync and sync was refusing to export it.

**The cause.** The provisioning log export showed the first step of every device attempt as `EntryImportDelete`: *Received computer '41677d01-...' change of type (Delete) from Active Directory*. The agent enforces a group scoping filter itself, before the cloud side evaluates anything, and returns an object that is not a member of any scope group as a delete. `HQ-WS001` was in no scope group. With nothing in the tenant to delete, the engine reported `JoinNotFound`. The later *Scoping filter evaluation passed* line is the cloud-side check and does not contradict this; the object had already been classed as a delete on the way in.

**The fix.** I created `APP-EntraCloudSync-Devices`, a global security group in `OU=Applications,OU=Groups`, at 2:58 PM and made `HQ-WS001` its only member, rather than putting a computer into a group named for users. Once it had replicated to `HQ-DC02`, which is the controller the agent reads from, the group's distinguished name was added as a second row in the scoping filter. Provisioning the device on demand then went green through all four steps: *Computer '41677d01-a299-4f17-8e29-675906799ac4' was created in Microsoft Entra ID*, with `deviceTrustType` `ServerAd`, `displayName` `HQ-WS001`, `deviceOSType` `Windows`, and `userCertificate` carried over.

**The join.** I ran the workstation's `Automatic-Device-Join` scheduled task through the guest agent. It succeeded on the first attempt at 3:02:54 PM: the User Device Registration log shows *Automatic registration Succeeded*, join type `DEVICE_AUTO`, and `dsregcmd /status` reports `AzureAdJoined : YES`, `DomainJoined : YES`, `DeviceId` `41677d01-a299-4f17-8e29-675906799ac4`, with the device key in the `Microsoft Platform Crypto Provider`, which is the TPM. The earlier attempts at 2:16 PM and 2:57 PM had failed with the not-found error, so the success is attributable to the export and nothing else.

The two admins who had written about `JoinNotFound` before this described a workstation with no registration certificate yet. That was not the case here, and the lesson is different: with group scoping, every computer that should hybrid join must be a member of a scope group, or the agent will never export it.

## Open

Everything this record set out to do is done: three users and one workstation from the directory exist in the tenant, the workstation is hybrid joined, the users are licensed, and a directory password signs in to Microsoft 365. What remains is cleanup and the next decision.

1. Give `testuser` a unique password. The sign-in proof it was kept for is complete, and a derivative of the break-glass domain password should not stay in the tenant longer than that proof needed. Listed with the rest of the restores in [Shared Test Password and Admin Policy Relaxation](Shared%20Test%20Password%20and%20Admin%20Policy%20Relaxation%20-%202026-09-10.md).
2. Decide when to move `DK-user@alphasecunited.com` from cloud-only onto the directory by soft match. The 2026-09-10 decision was to prove the path on `testuser` first; that condition is now met. Separate record when it happens.
3. Set `Credential Validation` auditing to include failures on both controllers, noted in the [agent install record](Entra%20Provisioning%20Agent%20Install%20-%202026-09-10.md).
