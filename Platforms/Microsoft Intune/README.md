# Microsoft Intune

**Created:** 2026-09-11  
**Last updated:** 2026-09-25

Intune is the device management plane for the `alphasecunited.com` tenant. It is the same tenant the [Active Directory](../Active%20Directory/README.md) forest synchronises into through Entra Cloud Sync, so identity comes from `ad.alphasecunited.com` and device management comes from here. The two are separate concerns and this record owns the second.

Apple device management has run since 2026-07-21, when I raised the Apple MDM push certificate. The iPad came in through Automated Device Enrollment and the MacBook Air M3 through the Company Portal on 2026-09-11.

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
| Administrator accounts | Cloud-only `DK-admin` holds Global Administrator since 2026-09-10; `BG-admin` is the break-glass account. Neither is excluded from any Conditional Access policy, because none exists |

## Managed devices

| Device | OS | Ownership | Enrollment path | Entra join type | Primary user | Enrolled |
|---|---|---|---|---|---|---|
| `dkadi-mb-air3` | macOS 26.6.2 (25G83) | Personal | Company Portal, user-initiated | Microsoft Entra registered | DK-user | 2026-09-11 |
| `iPad` | iPadOS 17.7.11 | Corporate | Automated Device Enrollment through Apple Business Manager | none shown | DK-user | 2026-09-07 |

The two differ in ownership. The iPad came through Apple Business Manager, so it is organisation-owned and supervised. The MacBook came through the Company Portal, so it is personally owned, unsupervised, and I can remove it from the Mac itself. `HQ-WS001` and `ObiPC` appear in Entra as hybrid joined but are not Intune managed and do not appear here.

Both Apple credentials expire on 7/21/2027 because they were raised on the same day. They renew separately, and the push certificate must be renewed with the Apple ID that created it. Renewing with a different Apple ID replaces the certificate instead, which would mean re-enrolling every Apple device.

## macOS enrollment

I enrolled the MacBook Air M3 on 2026-09-11 through the Company Portal without erasing it. Automated Device Enrollment would have needed an erase, because it runs inside Setup Assistant, and it would have made a personal laptop supervised and organisation-owned. The Mac is Microsoft Entra registered, not hybrid joined, and I can retire or wipe it from this console. The [enrollment record](Documentation/Change%20Records/MacBook%20Air%20M3%20Company%20Portal%20Enrollment%20-%202026-09-11.md) holds the prerequisites and verification.

## Decisions

**No compliance policy, false Compliant status accepted knowingly.** Decided 2026-09-11, the same day I enrolled the Mac.

Both managed devices report `Compliant`. Neither has been evaluated against anything. The tenant setting `Mark devices with no compliance policy assigned as` is `Compliant` and the tenant holds zero compliance policies on any platform, so the status is the built-in device compliance policy returning a default. Nothing has checked the Mac's disk encryption, OS version, or firewall, and nothing has checked the iPad either.

I am leaving it that way on purpose. I am not creating a compliance policy and I am not flipping the tenant default to `Not compliant`. Two devices, both mine, both of which I can inspect by hand faster than I can write a policy to inspect them. A compliance policy would be machinery reporting on a fleet of two that I already have eyes on.

What that costs:

- The `Compliant` column in both consoles carries no information. It is not evidence of anything and must not be cited as evidence in any record.
- Conditional Access requiring device compliance is off the table while this holds, for the reason in Open Items below.
- Device management still works. Enrollment bought visibility and the ability to push configuration, and that is intact. What is missing is enforcement and attestation, which is the part I am declining.

The decision to revisit is a fleet-size one. When this tenant manages devices I cannot personally inspect, or when somebody else's device enrolls, the reasoning above stops holding and a real compliance policy is the answer.

## Open Items

- **Do not create a Conditional Access policy that requires a compliant device.** This follows directly from the compliance decision above. Every device in this tenant reports Compliant without being evaluated, so such a policy would pass for the wrong reason and would start failing the moment a real compliance policy landed. Such a policy would also catch `DK-admin` and `BG-admin`, since neither has an exclusion, so that failure locks me out of my own tenant. This constraint stands until the compliance decision is revisited.
- Decide whether FileVault is enforced on the Mac with the recovery key escrowed into Intune. That mirrors the TPM+PIN BitLocker baseline open against the physical Windows workstation in the [Active Directory TODO](../Active%20Directory/Documentation/TODO.md), and settling both the same way keeps one disk-encryption posture across the fleet.
- Decide whether `HQ-WS001` and `ObiPC` should be Intune managed alongside AD Group Policy. I verified ObiPC's hybrid join and absence of MDM enrollment locally on 2026-09-12; [MDM options and proposed scope](Documentation/ObiPC%20MDM%20Options%20-%202026-09-12.md) recommend Intune. This is not Configuration Manager co-management. Enrollment remains undecided.
- Both Apple credentials expire 7/21/2027. Neither renews itself.

## Records

- [ObiPC MDM options and live checks - 2026-09-12](Documentation/ObiPC%20MDM%20Options%20-%202026-09-12.md)
- [MacBook Air M3 Company Portal Enrollment - 2026-09-11](Documentation/Change%20Records/MacBook%20Air%20M3%20Company%20Portal%20Enrollment%20-%202026-09-11.md)
- [S01 Tenant Readiness Readback - 2026-09-11](Evidence/MacBook%20Air%20M3%20Enrollment%20-%202026-09-11/Logs/S01%20Tenant%20Readiness%20Readback%20-%202026-09-11.md)
- [S02 Enrollment Verification - 2026-09-11](Evidence/MacBook%20Air%20M3%20Enrollment%20-%202026-09-11/Logs/S02%20Enrollment%20Verification%20-%202026-09-11.md)
- [Platform TODO](Documentation/TODO.md)
- [Active Directory](../Active%20Directory/README.md) for the forest, Entra Cloud Sync, and the hybrid-joined Windows workstations
