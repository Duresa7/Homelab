# S02 Enrollment Verification

**Created:** 2026-09-11  
**Last updated:** 2026-09-11

**Captured:** 2026-09-11, 11:40 PM to 11:55 PM Eastern  
**Target:** Microsoft Intune admin center and the Microsoft Entra device blade, tenant `alphasecunited.com`  
**Mechanism:** Google Chrome 152.0.7977.82 on `ubuntu-dev` (192.168.40.179), driven over the DevTools protocol on `127.0.0.1:9222` with `playwright-core`. Read-only. Covers screenshots S09 through S11. The readiness readback that preceded the enrollment is [S01](S01%20Tenant%20Readiness%20Readback%20-%202026-09-11.md), covering S01 through S08.

**Transcript boundary.** Browser readback, so no commands and no exit codes. Withheld identity values were replaced in the live DOM across every frame before each capture. For this log the substitution is driven by exact string matches taken from the alias map rather than by name patterns, after the pattern approach mislabelled the primary user on a first pass. A safety net also scans every frame for any remaining address that is neither an alias nor `testuser` and reports it; it returned empty for all three captures.

**Screenshot publication.** The eleven captures this job produced are retained on the host but are not published. Withheld identity values were substituted in the live DOM before each capture and an assertion confirmed none survived in any frame, but no human has reviewed all eleven images, and this repository is public. The rule is the one the Active Directory evidence already follows: the negation line for this folder's `Screenshots/` stays commented in `.gitignore` until the images are checked by hand. The values each image shows are transcribed in full below, so nothing in this log depends on seeing them.

**The enrollment itself was performed by hand on the Mac** and has no retained capture from the device side. Apple requires the management profile to be approved in the interface, so there is no command to record. What follows verifies the result from the two consoles.

## S09 Intune device list

**Action.** Opened Devices, All devices, and clicked Refresh.

**Result.** 2 devices.

| Device name | Managed by | Ownership | Compliance | OS | OS version | Primary user UPN | Last check-in |
|---|---|---|---|---|---|---|---|
| `dkadi-mb-air3` | Intune | Personal | Compliant | macOS | 26.6.2 (25G83) | DK-user | 09/11/2026, 11:36 PM |
| `iPad` | Intune | Corporate | Compliant | iOS/iPadOS | 17.7.11 | DK-user | 09/11/2026, 11:18 PM |

**Verification.** The Mac is enrolled and managed by Intune. Ownership reads `Personal`, which is correct for a user-initiated Company Portal enrollment and is the distinction from the iPad, which came in through Automated Device Enrollment and reads `Corporate`. The primary user is DK-user, which is the account holding the Business Premium seat and therefore the Intune licence. The enrolled device count moved from 1 to 2.

**Capture.** `Screenshots/S09-Intune-All-Devices-After-macOS-Enrollment-2026-09-11.png`

## S10 Entra device list

**Action.** Opened the Microsoft Entra devices blade and clicked Refresh.

**Result.** 4 devices.

| Name | Enabled | OS | Version | Join type | MDM | Compliant | Registered |
|---|---|---|---|---|---|---|---|
| `iPad` | Yes | IPad | 17.7.11 | none shown | Microsoft Intune | N/A | N/A |
| `dkadi-mb-air3` | Yes | MacMDM | 26.6.2 (25G83) | Microsoft Entra registered | Microsoft Intune | Yes | 9/11/2026, 11:35 PM |
| `HQ-WS001` | Yes | Windows | 10.0.26200.9445 | Microsoft Entra hybrid joined | None | N/A | N/A |
| `ObiPC` | Yes | Windows | 10.0.26200.9445 | Microsoft Entra hybrid joined | None | N/A | N/A |

**Verification.** The join type reads `Microsoft Entra registered`, which is the expected and correct end state for a Mac. Hybrid join is Windows only, which is why the two Windows workstations read differently and why the forest played no part in this enrollment. The device registered at 11:35 PM and checked in to Intune at 11:36 PM, one minute apart.

**Capture.** `Screenshots/S10-Entra-All-Devices-After-macOS-Enrollment-2026-09-11.png`

## S11 Compliance settings

**Action.** Opened Devices, Compliance, Compliance settings.

**Result.** `Mark devices with no compliance policy assigned as` reads `Compliant`.

**Verification.** This explains the `Compliant` status both devices show while the tenant holds zero compliance policies. The status is the built-in device compliance policy returning the tenant default, not the result of any check against the Mac. Nothing has evaluated the Mac's disk encryption, OS version, or firewall, because no policy exists to do so. The Entra blade reporting `Compliant: Yes` for the Mac carries the same caveat.

**Capture.** `Screenshots/S11-Intune-Compliance-Settings-2026-09-11.png`

## Resulting state

`dkadi-mb-air3` is enrolled in Intune as a personally owned macOS device on macOS 26.6.2 (25G83), Microsoft Entra registered, primary user DK-user, first check-in 09/11/2026 11:36 PM Eastern. The tenant now manages 2 devices. No erase was performed and no tenant setting was changed during this verification.

The compliance status on both devices is the tenant default rather than a real evaluation. That is recorded as an open item in the [platform README](../../../README.md).
