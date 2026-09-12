# Microsoft Intune

**Created:** 2026-09-11  
**Last updated:** 2026-09-11

Intune is the device management plane for the `alphasecunited.com` tenant. It is the same tenant the [Active Directory](../Active%20Directory/README.md) forest synchronises into through Entra Cloud Sync, so identity comes from `ad.alphasecunited.com` and device management comes from here. The two are separate concerns and this record owns the second.

Apple device management was already in service before this record existed: the Apple MDM push certificate was raised on 2026-07-21 and the iPad was enrolled through Automated Device Enrollment. I wrote this record on 2026-09-11, when I audited the tenant to find out whether I could enroll my MacBook Air M3 without erasing it and then did so.

## Current State

| Item | Current value |
|---|---|
| Tenant | `alphasecunited.com`, North America 0801 |
| MDM authority | Microsoft Intune |
| Account status | Active |
| Service release | 2608 |
| Intune licences | 1 total, 1 assigned to DK-user |
| Enrolled devices | 2 |
| Apple MDM push certificate | Active, raised 7/21/2026, expires 7/21/2027, serial `694C64103FE87817` |
| Apple Business Manager | Connected. Token `AlphaSec United MS365 Intune`, Active, 1 device synced, expires 7/21/2027 |
| Enrollment platform restrictions | One policy, the built-in `All Users` default, assigned to All devices, every platform allowed |
| Enrollment device limit | 5 devices per user, one policy covering all users and all devices |
| Compliance policies | None. The tenant marks devices with no policy assigned as Compliant |
| Conditional Access policies | None |

## Managed devices

| Device | OS | Ownership | Enrollment path | Entra join type | Primary user | Enrolled |
|---|---|---|---|---|---|---|
| `dkadi-mb-air3` | macOS 26.6.2 (25G83) | Personal | Company Portal, user-initiated | Microsoft Entra registered | DK-user | 2026-09-11 |
| `iPad` | iPadOS 17.7.11 | Corporate | Automated Device Enrollment through Apple Business Manager | none shown | DK-user | 2026-09-07 |

The ownership split is the real difference between the two. The iPad came through Apple Business Manager, so it is organisation-owned and supervised. The MacBook came through the Company Portal, so it is personally owned, unsupervised, and I can remove it from the Mac itself. `HQ-WS001` and `ObiPC` appear in Entra as hybrid joined but are not Intune managed and do not appear here.

Both Apple credentials expire on 7/21/2027 because they were raised on the same day. They renew separately, and the push certificate must be renewed with the Apple ID that created it. Renewing with a different Apple ID replaces the certificate instead, which would mean re-enrolling every Apple device.

## macOS enrollment

I settled one question on 2026-09-11: can an already configured MacBook Air M3 join this tenant without being wiped. It can, and it did. The path is user-initiated enrollment with the Company Portal, and every prerequisite was already in place before I started:

- The Apple MDM push certificate was Active with 313 days remaining, and one push certificate covers every Apple platform in a tenant rather than just the iPad it was raised for.
- macOS and personally owned macOS were both allowed by the only platform restriction, with no minimum version floor.
- The device limit is 5 per user against 1 device enrolled at the time.
- One Intune licence exists, assigned to DK-user. Microsoft 365 Business Premium carries Intune Plan 1, which is the right that enrollment draws on.

Automated Device Enrollment is the path that would have required an erase, because it runs inside Setup Assistant. It did not apply. A personally bought Mac is not in Apple Business Manager, and the one device the ADE token has synced is the iPad. Adding a Mac to Apple Business Manager after purchase needs Apple Configurator and an erase anyway, and it would make a personal laptop supervised and organisation-owned, which is not what I want for this machine.

The Mac is Microsoft Entra registered rather than hybrid joined. Hybrid join is Windows only, so the forest played no part. The Mac authenticates to Entra directly with the password-hash-synced password. It registered at 11:35 PM and checked in to Intune at 11:36 PM on 2026-09-11.

The approval of the management profile has to happen in the interface on the machine. macOS 11 removed the ability to install an MDM enrollment profile from the command line on an unsupervised Mac, so there is no remote or scripted path to this step and no captured evidence from the device side. Verification is from the two consoles instead.

Two consequences of managing a personal machine, stated plainly. I can retire or wipe `dkadi-mb-air3` from this console, and macOS has no app-protection-only enrollment, so it is full MDM or nothing. Signing into Edge or the Office apps without the Company Portal would have given Entra registration and single sign-on without management, which remains the lighter option for any future personal device.

## Decisions

**No compliance policy, false Compliant status accepted knowingly.** Decided 2026-09-11, the same day I enrolled the Mac.

Both managed devices report `Compliant`. Neither has been evaluated against anything. The tenant setting `Mark devices with no compliance policy assigned as` is `Compliant` and the tenant holds zero compliance policies on any platform, so the status is the built-in device compliance policy returning a default. Nothing has checked the Mac's disk encryption, OS version, or firewall, and nothing has checked the iPad either.

I am leaving it that way on purpose. I am not creating a compliance policy and I am not flipping the tenant default to `Not compliant`. Two devices, both mine, both of which I can inspect by hand faster than I can write a policy to inspect them. A compliance policy would be machinery reporting on a fleet of two that I already have eyes on.

What I am buying with that, and what I am giving up, stated so the next reader does not have to work it out:

- The `Compliant` column in both consoles carries no information. It is not evidence of anything and must not be cited as evidence in any record.
- Conditional Access requiring device compliance is off the table while this holds, for the reason in Open Items below.
- Device management still works. Enrollment bought visibility and the ability to push configuration, and that is intact. What is missing is enforcement and attestation, which is the part I am declining.

The decision to revisit is a fleet-size one. When this tenant manages devices I cannot personally inspect, or when somebody else's device enrolls, the reasoning above stops holding and a real compliance policy is the answer.

## Open Items

- **Do not create a Conditional Access policy that requires a compliant device.** This follows directly from the compliance decision above. Every device in this tenant reports Compliant without being evaluated, so such a policy would pass for the wrong reason and would start failing the moment a real compliance policy landed. The tenant has one admin account and no break-glass exclusion, so that failure locks me out of my own tenant. This constraint stands until the compliance decision is revisited.
- Decide whether FileVault is enforced on the Mac with the recovery key escrowed into Intune. That mirrors the BitLocker baseline open against the physical Windows workstation in the [Active Directory TODO](../Active%20Directory/Documentation/TODO.md), and settling both the same way keeps one disk-encryption posture across the fleet.
- Decide whether `HQ-WS001` and `ObiPC` should be co-managed. Both are Entra hybrid joined through Cloud Sync device sync and both read `MDM: None`, so the tenant manages no Windows endpoint.
- Both Apple credentials expire 7/21/2027. Neither renews itself.

## Records

- [MacBook Air M3 Company Portal Enrollment - 2026-09-11](Documentation/Change%20Records/MacBook%20Air%20M3%20Company%20Portal%20Enrollment%20-%202026-09-11.md)
- [S01 Tenant Readiness Readback - 2026-09-11](Evidence/MacBook%20Air%20M3%20Enrollment%20-%202026-09-11/Logs/S01%20Tenant%20Readiness%20Readback%20-%202026-09-11.md)
- [S02 Enrollment Verification - 2026-09-11](Evidence/MacBook%20Air%20M3%20Enrollment%20-%202026-09-11/Logs/S02%20Enrollment%20Verification%20-%202026-09-11.md)
- [Platform TODO](Documentation/TODO.md)
- [Active Directory](../Active%20Directory/README.md) for the forest, Entra Cloud Sync, and the hybrid-joined Windows workstations
