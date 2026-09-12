# S01 Tenant Readiness Readback

**Created:** 2026-09-11  
**Last updated:** 2026-09-11

**Captured:** 2026-09-11, 10:15 PM to 10:45 PM Eastern  
**Target:** Microsoft Intune admin center, tenant `alphasecunited.com`  
**Mechanism:** Google Chrome 152.0.7977.82 on `ubuntu-dev` (192.168.40.179), driven over the DevTools protocol on `127.0.0.1:9222` with `playwright-core`. Read-only throughout: I opened blades and read them back, and changed no tenant setting.

**Transcript boundary.** This is a browser readback, so there are no commands and no exit codes to retain. Each step below records the blade I opened and the values it showed. Before every screenshot I replaced the withheld identity values in the live DOM across every frame, including the cross-origin ones the blades render inside, then asserted that no withheld string survived anywhere in the page. That assertion returned empty for every capture that contains one. The signed-in account reads `DK-admin` and the Apple ID reads `DK-appleid` in all eight images because of that substitution, not because the tenant holds those strings.

**Screenshot publication.** The eleven captures this job produced are retained on the host but are not published. Withheld identity values were substituted in the live DOM before each capture and an assertion confirmed none survived in any frame, but no human has reviewed all eleven images, and this repository is public. The rule is the one the Active Directory evidence already follows: the negation line for this folder's `Screenshots/` stays commented in `.gitignore` until the images are checked by hand. The values each image shows are transcribed in full below, so nothing in this log depends on seeing them.

**Sign-in.** I signed in by hand in the browser window. The password and the second factor never entered any captured output.

## S01 Apple MDM push certificate

**Action.** Opened Devices, Enroll devices, Apple enrollment, then the Apple MDM Push Certificate prerequisite.

**Result.**

| Field | Value |
|---|---|
| Status | Active |
| Last updated | 7/21/2026 |
| Expiration | 7/21/2027 |
| Days until expiration | 313 |
| Serial number | `694C64103FE87817` |
| Apple ID | DK-appleid |

**Failure worth recording.** My first two attempts to open this blade clicked a matching string in the top-level document instead of the button inside the `Enrollment.ReactView` frame, and captured the list page rather than the certificate. The capture below is the third attempt, made after targeting the child frame directly. The first two images were overwritten rather than retained.

**Verification.** The blade reports Active with a 2027 expiry, so the certificate covers macOS as well as the enrolled iPad. A single push certificate serves every Apple platform in a tenant.

**Capture.** `Screenshots/S01-Intune-Apple-MDM-Push-Certificate-2026-09-11.png`

## S02 Enrollment program tokens

**Action.** Opened the Enrollment program tokens blade.

**Result.** One token.

| Field | Value |
|---|---|
| Token name | `AlphaSec United MS365 Intune` |
| Status | Active |
| Program type | Apple Business Manager |
| Apple ID | DK-appleid |
| Devices synced | 1 |
| Last sync | 09/11/2026, 02:34 PM |
| Expiration date | 07/21/2027, 04:10 PM |
| Scope tags | Default |

**Verification.** Apple Business Manager is connected and syncing, and it has claimed exactly one device. That device is the enrolled iPad. A personally purchased Mac is not in Apple Business Manager, so no Automated Device Enrollment profile will claim it and no erase is forced.

**Capture.** `Screenshots/S02-Intune-Enrollment-Program-Tokens-2026-09-11.png`

## S03 Enrollment device platform restrictions, list

**Action.** Opened Enrollment device platform restrictions and selected the macOS restrictions tab.

**Result.** One policy under Device type restrictions: priority `Default`, name `All Users`, assigned `Yes`. No custom restriction exists on any platform tab.

**Verification.** With only the built-in default present, nothing can override it at a higher priority, so the default alone decides whether a Mac may enroll.

**Capture.** `Screenshots/S03-Intune-Enrollment-Device-Platform-Restrictions-2026-09-11.png`

## S04 macOS platform restriction properties

**Action.** Opened the `All Users` default restriction, then Properties.

**Result.** Platform `AllPlatforms`. Description reads that this is the default Device Type Restriction applied with lowest priority to all users regardless of group membership. Assigned to group `All devices`, status Active.

| Type | Platform | Min | Max | Personally owned | Blocked manufacturers |
|---|---|---|---|---|---|
| Android Enterprise (work profile) | Allow | | | Allow | |
| Android device administrator | Allow | | | Allow | |
| iOS/iPadOS | Allow | | | Allow | N/A |
| visionOS | Allow | N/A | N/A | N/A | N/A |
| tvOS | Allow | N/A | N/A | N/A | N/A |
| macOS | Allow | N/A | N/A | Allow | N/A |
| Windows (MDM) | Allow | | | Allow | N/A |

**Verification.** macOS reads Allow on both the platform and the personally owned column, with no minimum version. This is the setting that would have blocked the enrollment, and it does not.

**Capture.** `Screenshots/S04-Intune-macOS-Platform-Restriction-Properties-2026-09-11.png`

## S05 Enrollment device limit restrictions

**Action.** Opened Enrollment device limit restrictions.

**Result.** One restriction, `All users and all devices`, device limit `5`, assigned `Yes`.

**Verification.** One device is enrolled against a limit of 5, so the Mac would be the second of five. The limit is not a constraint here.

**Capture.** `Screenshots/S05-Intune-Enrollment-Device-Limit-Restrictions-2026-09-11.png`

## S06 Compliance policies

**Action.** Opened Devices, Compliance, Policies.

**Result.** `0 policies`. The grid reads `No compliance policies found`.

**Verification.** No compliance policy exists on any platform. This explains the `Compliant: N/A` the iPad shows in the Entra device list, and it means an enrolled Mac will also carry no compliance state until a policy is created and assigned.

**Capture.** `Screenshots/S06-Intune-Compliance-Policies-2026-09-11.png`

## S07 Conditional Access policies

**Action.** Opened Conditional Access, Policies.

**Result.** No policies. The blade shows its first-run state, offering to create a first policy.

**Verification.** No Conditional Access policy exists, so enrolling a device cannot trigger an access block, and nothing currently consumes the compliance signal. The lockout risk is not present today and would only appear if a policy requiring a compliant device were created before a macOS compliance policy existed.

**Capture.** `Screenshots/S07-Intune-Conditional-Access-Policies-2026-09-11.png`

## S08 Tenant status

**Action.** Opened Tenant administration, Tenant status, Tenant details.

**Result.**

| Field | Value |
|---|---|
| Tenant name | `alphasecunited.com` |
| Tenant location | North America 0801 |
| MDM authority | Microsoft Intune |
| Account status | Active |
| Service release | 2608 |
| Total licensed users | 1 |
| Total Intune licences | 1 |
| Total enrolled devices | 1 |

**Verification.** One Intune licence exists and is assigned, and the MDM authority is Intune rather than a co-existing authority. The enrolled device count of 1 matches the single iPad and confirms that neither Windows workstation is Intune managed.

**Capture.** `Screenshots/S08-Intune-Tenant-Status-2026-09-11.png`

## Resulting state

Nothing in the tenant changed. Every prerequisite for a user-initiated macOS enrollment is in place: the push certificate is Active until 7/21/2027, macOS and personally owned macOS are allowed, the device limit has room, and a licence is assigned. The two gaps the audit surfaced are the absence of any compliance policy and the absence of any Conditional Access policy, both recorded in the [platform README](../../../README.md).
