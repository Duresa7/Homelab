# Microsoft Intune TODO

**Created:** 2026-09-11  
**Last updated:** 2026-09-11

I keep the detailed list for Intune and device management here. The root TODO.md links here for the steps and completion checks.

## Conditional Access, standing constraint

This is not a task. It is a rule that follows from the compliance decision of 2026-09-11 recorded in the [platform README](../README.md), and it holds until that decision is revisited.

1. I will not create any Conditional Access policy that requires a compliant device. Every device in this tenant reports Compliant without being evaluated, so the policy would pass for the wrong reason today and would begin failing the moment a real compliance policy landed. With one admin account and no break-glass exclusion, that failure locks me out of my own tenant.
2. If I ever build a Conditional Access policy for any other purpose, I will create the break-glass exclusion first and confirm it works before enabling the policy. This step is done when a second path into the tenant is proven to survive the policy being on.

## FileVault with recovery key escrow (decision open)

1. I will decide whether Intune enforces FileVault on `dkadi-mb-air3` with the recovery key escrowed into Intune. This mirrors the TPM-only BitLocker baseline still open for the physical Windows workstation in the [Active Directory TODO](../../Active%20Directory/Documentation/TODO.md), and settling both the same way keeps one disk-encryption posture across the fleet. The decision is done when I record the baseline and its scope.
2. If I enforce it, I will confirm the recovery key is retrievable from the Intune console before I rely on it. A key escrow I have never read back is not a recovery path. This step is done when I have retrieved the key once and recorded that it worked, without recording the key.

## Platform SSO (optional, not started)

1. I will decide whether to configure Platform SSO on the Mac. It links the local macOS account to Entra with Secure Enclave backed keys and changes the Entra join type from registered to joined. This is a follow-on to the enrollment rather than part of it. The decision is done when I record whether I want it.
2. If I configure it, I will choose the authentication method deliberately. The Password method syncs the local login password with the Entra password, which is a meaningful change to how I sign in to my own laptop. The Secure Enclave method leaves the local password alone. This step is done when the method is recorded alongside the configuration.

## Windows co-management (separate work, not started)

1. I will decide whether `HQ-WS001` and `ObiPC` should be Intune managed. Both are Microsoft Entra hybrid joined through Cloud Sync device sync and both read `MDM: None`, so the tenant manages no Windows endpoint. The decision is done when I record whether co-management is wanted.
2. If it is, the mechanism is the MDM user scope in Entra plus the automatic enrollment Group Policy against the hybrid-joined machines. This step is done when at least one workstation reports MDM `Microsoft Intune` and I have verified it from both consoles.

## Apple credential renewals (dated, 2027)

1. Both Apple credentials expire on 7/21/2027 because both were raised on 7/21/2026. The Apple MDM push certificate expires that day and the Apple Business Manager token expires at 04:10 PM the same day. Neither renews itself.
2. The push certificate must be renewed with the same Apple ID that created it. Renewing with a different Apple ID replaces the certificate rather than renewing it, and every enrolled Apple device would have to be re-enrolled. The Apple ID is recorded in the alias map as DK-appleid. This item is done when both are renewed and the new expiry dates are recorded in the platform README.

## Done in this build, kept here for the record

1. 2026-09-11: I audited the tenant for macOS enrollment readiness and confirmed all four prerequisites. [S01 Tenant Readiness Readback](../Evidence/MacBook%20Air%20M3%20Enrollment%20-%202026-09-11/Logs/S01%20Tenant%20Readiness%20Readback%20-%202026-09-11.md).
2. 2026-09-11: I enrolled `dkadi-mb-air3` through the Company Portal without erasing it, and verified it from both consoles as personally owned, Microsoft Entra registered, primary user DK-user. [MacBook Air M3 Company Portal Enrollment](Change%20Records/MacBook%20Air%20M3%20Company%20Portal%20Enrollment%20-%202026-09-11.md).
3. 2026-09-11: I confirmed the Compliant status on both devices comes from the tenant default rather than any evaluation, which is what forced the compliance decision recorded as item 4.
4. 2026-09-11: I decided against a macOS compliance policy and accepted the false Compliant status knowingly, rather than creating a policy or flipping the tenant default to `Not compliant`. The reasoning and what it costs are in the [platform README](../README.md). The standing Conditional Access constraint above is the consequence.
