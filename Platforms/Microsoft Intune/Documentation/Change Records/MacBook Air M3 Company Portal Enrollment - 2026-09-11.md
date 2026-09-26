# MacBook Air M3 Company Portal Enrollment

**Created:** 2026-09-11  
**Last updated:** 2026-09-25

**Event date:** 2026-09-11

I enrolled my personal MacBook Air M3 into the `alphasecunited.com` tenant through the Intune Company Portal, without erasing it. The machine keeps its existing local account, files, applications, and Apple ID. It is the tenant's second managed device and its first macOS device.

## Why this way

I wanted the Mac managed alongside the iPad, and I was not willing to wipe a working personal laptop to get there. Those two goals are compatible because Apple offers two enrollment paths and only one of them needs a clean machine.

Automated Device Enrollment runs inside Setup Assistant, so it applies to a device that is either new or freshly erased. It also requires the device to be in Apple Business Manager, and adding a personally bought Mac to Apple Business Manager after the fact needs Apple Configurator and an erase of its own. On top of that it would make the laptop supervised and organisation-owned, which is the wrong posture for a machine I bought myself.

User-initiated enrollment through the Company Portal has neither constraint. It installs a management profile onto a running, configured Mac and leaves everything else alone. The device comes out personally owned and unsupervised, which is what I want, and I can remove it from the Mac itself rather than needing the console.

## What I checked first

I audited the tenant before touching the laptop, because a failed enrollment attempt against a blocking restriction is a worse way to learn the answer. The full readback is in [S01](../../Evidence/MacBook%20Air%20M3%20Enrollment%20-%202026-09-11/Logs/S01%20Tenant%20Readiness%20Readback%20-%202026-09-11.md), covering screenshots S01 through S08. Four prerequisites, all already satisfied:

| Prerequisite | Observed | Why it matters |
|---|---|---|
| Apple MDM push certificate | Active, expires 7/21/2027, 313 days left | Without it no Apple device can enroll at all. One certificate covers every Apple platform, so the one raised for the iPad already covered macOS |
| macOS platform restriction | `Allow`, personally owned `Allow`, no version floor | This is the setting that would have blocked the enrollment outright |
| Device limit | 5 per user, 1 device enrolled | The Mac becomes the second of five |
| Intune licence | 1 total, 1 assigned to DK-user | Business Premium carries Intune Plan 1, which is the right enrollment consumes |

I also confirmed the Apple Business Manager token had synced exactly one device, the iPad, which ruled out any ADE profile trying to claim the Mac.

## What I did

1. Installed Company Portal for macOS from the installer Microsoft publishes, `CompanyPortal-Installer.pkg`, 85,659,163 bytes.
2. Signed in as DK-user rather than DK-admin, because DK-user holds the Business Premium seat and the Intune licence, and enrolling as the daily account puts the device under the right primary user.
3. Completed the enrollment prompt and approved the management profile in System Settings, Privacy and Security, Profiles.

Step 3 has to happen in the interface on the machine. macOS 11 removed the ability to install an MDM enrollment profile from the command line on an unsupervised Mac, so there is no scripted or remote path to it and no retained capture from the device side. Everything below verifies the result from the two consoles instead.

## What I verified

The console verification is in [S02](../../Evidence/MacBook%20Air%20M3%20Enrollment%20-%202026-09-11/Logs/S02%20Enrollment%20Verification%20-%202026-09-11.md), covering screenshots S09 through S11.

**Intune device list** now holds 2 devices:

| Device name | Managed by | Ownership | OS | OS version | Primary user UPN | Last check-in |
|---|---|---|---|---|---|---|
| `dkadi-mb-air3` | Intune | Personal | macOS | 26.6.2 (25G83) | DK-user | 09/11/2026, 11:36 PM |
| `iPad` | Intune | Corporate | iOS/iPadOS | 17.7.11 | DK-user | 09/11/2026, 11:18 PM |

Ownership reading `Personal` against the iPad's `Corporate` is the visible consequence of the two enrollment paths, and confirms the Mac came in unsupervised as intended.

**Entra device list** now holds 4 devices, and `dkadi-mb-air3` reads:

| Field | Value |
|---|---|
| Join type | Microsoft Entra registered |
| OS | MacMDM 26.6.2 (25G83) |
| MDM | Microsoft Intune |
| Security settings management | Microsoft Intune |
| Registered | 9/11/2026, 11:35 PM |

Registered is the correct end state, not a partial one. Hybrid join is Windows only, which is why `HQ-WS001` and `ObiPC` read `Microsoft Entra hybrid joined` in the same list and the Mac cannot. The forest played no part in this: the Mac authenticates to Entra directly using the password-hash-synced password.

The device registered at 11:35 PM and checked in to Intune at 11:36 PM, one minute apart.

**Nothing was erased.** The local account, files, applications, and Apple ID are unchanged. The only addition is the management profile.

## What this did not do

The Mac shows `Compliant`, and that status is not a real result. The tenant setting `Mark devices with no compliance policy assigned as` is `Compliant`, and the tenant holds zero compliance policies on any platform. Nothing has evaluated the Mac's disk encryption, OS version, or firewall. The iPad carries the same false green. I confirmed the setting directly rather than inferring it, captured as S11.

Enrollment on its own therefore buys visibility and the ability to push configuration. It buys no enforcement until a compliance policy exists.

## Open

- Settled the same day: I decided against a macOS compliance policy and accepted the false Compliant status knowingly. The reasoning is in the [platform README](../../README.md). The `Compliant` column carries no information and is not evidence of anything.
- Standing constraint from that decision: no Conditional Access policy may require a compliant device. Such a policy would pass for the wrong reason today and would begin failing the moment a real compliance policy landed, which would catch both `DK-admin` and the break-glass `BG-admin`, since neither is excluded, and lock me out of my own tenant.
- Decide whether FileVault is enforced with the recovery key escrowed into Intune, alongside the BitLocker baseline still open for the physical Windows workstation.

Steps and completion checks are in the [platform TODO](../TODO.md).
