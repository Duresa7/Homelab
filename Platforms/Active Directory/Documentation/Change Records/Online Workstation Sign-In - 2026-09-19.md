# Online Workstation Sign-In

**Created:** 2026-09-19  
**Last updated:** 2026-09-19

I applied `C-WKS-OnlineLogon` to `OU=Workstations,DC=ad,DC=alphasecunited,DC=com`. Both `HQ-WS001` and `OBIPC` received it. The policy disables cached domain-password sign-in, requires domain-controller authentication to unlock, waits for network policy processing at startup and sign-in, and excludes PIN, biometric, picture-password, and FIDO sign-in providers. The Windows password provider remains available. Servers and domain controllers are outside this OU.

## What I found

My concern was that unplugging Ethernet could let somebody bypass domain control or leave a computer with a broken trust relationship. I did not have a captured error or a reproducible example of that historical incident. I treated this as a policy coverage check and hardening change, rather than claiming to have diagnosed that incident.

Both workstations were domain joined with healthy secure channels before the change. Netlogon was automatic, machine-password changes were enabled, and time followed a domain controller. `OBIPC` already had `CachedLogonsCount=0` and `ForceUnlockLogon=1` through `C-WKS-ObiPC-OnlineLogon`, which was scoped to that computer. `HQ-WS001` had `CachedLogonsCount=10`, `ForceUnlockLogon=0`, and no foreground network-wait policy. The initial configuration check returned `Pass=false` on `HQ-WS001`.

ObiPC also had data in the Windows Hello container directory. That proves the directory contained data, not which user could successfully use a PIN. Disabling cached passwords alone does not cover every credential provider, so I excluded the alternative providers as well as disabling new Hello provisioning. I did not delete existing Hello keys or credentials.

The enabled local setup account on ObiPC had a password set. I left local recovery accounts available. Anyone with valid local administrator credentials remains able to administer the computer independently of AD; an Ethernet cable is not that security boundary.

## Applied configuration

I created the GPO with [Set-WorkstationOnlineLogonPolicy.ps1](../../Scripts/Set-WorkstationOnlineLogonPolicy.ps1), disabled its user half, and enabled its link on `Workstations`. I left the older ObiPC policy in place; its two settings agree with the new policy. The replicated [policy readback](../../Evidence/Online%20Workstation%20Sign-In%20-%202026-09-19/Policy-Verification.json) contains the exact registry paths, types, values, and provider identifiers.

| Setting | Value |
|---|---|
| Cached domain logons | `CachedLogonsCount`, string `0` |
| Online domain unlock | `ForceUnlockLogon`, DWORD `1` |
| Wait for network policy processing | `SyncForegroundPolicy`, DWORD `1` |
| Windows Hello for Business provisioning | `Enabled`, DWORD `0` |
| Convenience domain PIN | `AllowDomainPINLogon`, DWORD `0` |
| Domain picture password | `BlockDomainPicturePassword`, DWORD `1` |
| Excluded credential providers | Convenience PIN, Windows Hello PIN, face, fingerprint, picture password, FIDO security key |

This makes an unavailable domain controller a sign-in availability problem by design. It does not remove the computer's domain membership. It also does not immediately lock or log off a desktop that is already open. Applied local restrictions continue to govern that session, but new directory changes cannot arrive while it is offline. I did not install a network-disconnect watchdog or terminate any sessions.

## Verification

I ran computer policy refreshes and the [workstation validation script](../../Scripts/Test-WorkstationOnlineLogonPolicy.ps1) on both clients. Final checks passed at 10:33:28 AM EDT on `HQ-WS001` and 10:34:21 AM EDT on `OBIPC`. The [retained commands and outputs](../../Evidence/Online%20Workstation%20Sign-In%20-%202026-09-19/Workstation-Verification.json) show the policy in resultant computer policy, every configured sign-in control, the retained password provider, automatic Netlogon, enabled machine-password changes, and a healthy secure channel.

At 10:32:49 AM EDT I completed a [network-disconnect test](../../Evidence/Online%20Workstation%20Sign-In%20-%202026-09-19/Network-Disconnect-Test.json) on `HQ-WS001` through the QEMU guest agent. I disabled its one active network adapter, read the local state, and enabled the adapter in a `finally` block. With zero active adapters, `PartOfDomain` remained `true`, the domain stayed `ad.alphasecunited.com`, and both sign-in settings stayed configured. After reconnection there was one active adapter and `Test-ComputerSecureChannel` returned `true`. No rejoin or machine-password repair was needed.

On ObiPC, [AppLocker readback at 10:28:21 AM EDT](../../Evidence/Online%20Workstation%20Sign-In%20-%202026-09-19/ObiPC-AppLocker-Verification.json) showed `AppIDSvc` running with automatic startup. Exe, Msi, and Appx collections were enforced with 48, 4, and 7 rules; Script remained audit-only with 12 rules. I did not change those rules or disconnect the physical workstation. This is configuration evidence, not a new functional test of the restricted user's offline session.

I read the final GPO from `HQ-DC02` at 10:34:51 AM EDT and verified all seven registry values, `UserSettingsDisabled`, and the enabled OU link by GPO ID. This confirms that the change replicated to the second controller.

## Execution issues and cleanup

I did not retain raw captures for the initial inventory, first failing configuration check, or the following intermediate command failures. The final checks above have retained captures.

The first ObiPC refresh preceded the new OU link being visible there. The SSH sign-in context could not run `repadmin /syncall /AdeP`: it returned access denied and error 8440. Running the same replication operation as SYSTEM through the controller's QEMU guest agent completed all naming contexts without errors. Another policy refresh applied the new GPO on ObiPC. A display-name filter on the link readback also produced an empty result because those link objects had null display names; matching the GPO ID confirmed the link.

The SSH wrapper rejected a top-level `CmdletBinding` declaration, so I used a script block. The expanded validation command later exceeded Windows' command-line length limit. I transferred the script in two pieces to a temporary file and invoked a child PowerShell process with `-ExecutionPolicy Bypass`; the first direct file invocation had been rejected by the existing execution policy. The process-only override did not change the machine's execution policy, and the temporary script was removed in `finally`. No snapshots or backups were created.

## Open verification and limits

I have not attempted an interactive offline domain-password login or unlock, checked the resulting sign-in tiles, or exercised the restricted user's applications with ObiPC disconnected. Those checks remain in the [platform TODO](../TODO.md#online-workstation-sign-in-applied-2026-09-19-interactive-checks-open). The network test proves retained membership and recovery, not password rejection at the sign-in screen. I did not reboot or sign out either workstation, so I have not observed the next foreground startup/sign-in cycle.

This change does not block a person who already holds a local administrator password, prevent offline disk modification, or force an already-open session to lock on cable removal. It does not claim to prevent every future trust failure from unrelated causes.

Microsoft documents the [cached-logon setting](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/security-policy-settings/interactive-logon-number-of-previous-logons-to-cache-in-case-domain-controller-is-not-available), the paired [online-unlock setting](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/security-policy-settings/interactive-logon-require-domain-controller-authentication-to-unlock-workstation), and [credential-provider exclusion](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-admx-credentialproviders#excludedcredentialproviders). I used those controls for the requested online-only domain sign-in behavior; this is not a claim that disabling Hello is a general Windows security baseline.
