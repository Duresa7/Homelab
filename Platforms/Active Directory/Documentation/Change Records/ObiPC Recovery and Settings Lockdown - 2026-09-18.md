# ObiPC Recovery and Settings Lockdown

**Created:** 2026-09-18  
**Last updated:** 2026-09-19

On 2026-09-18 `IK-user` wiped `ObiPC` from the Windows recovery menu, which on Windows 11 offers a full reset with no credentials; the account of that is the [incident report](../../../../Security/Incidents/Active%20Directory/ObiPC%20Wiped%20from%20the%20Recovery%20Menu%20-%202026-09-18.md). This record is the response, applied the same night after the [rebuild](ObiPC%20Rebuild%20and%20Rejoin%20-%202026-09-18.md) in two passes: close every path from a standard user to a reset, a reinstall, the recovery environment or Safe Mode, take away every setting on the machine that is administrative or changes its state, and then, in the second pass, make [Action1](../../../Action1/README.md) the only way software reaches this account, by closing the developer carve-out that would have let a downloaded program run. It extends the [2026-09-12 restriction work](ObiPC%20Restricted%20User%20Setup%20-%202026-09-12.md); the two role groups, the loopback design and the developer carve-out are unchanged. **It is in force** on the machine as of 11:14 PM. The user side takes effect when `IK-user` next signs in, which he has not done since the rebuild.

## What I researched first

I read Microsoft's documentation for the recovery environment, the Settings and Control Panel policies, the App Installer and package deployment policies, and AppLocker, together with the published AppLocker bypass lists, before changing anything. Three findings shaped the design:

1. **The reset is a documented default.** `Security/RecoveryEnvironmentAuthentication` defaults to "Remove everything: no authentication required" ([Security Policy CSP](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-security)). The policy has no Group Policy template. On this build, though, the PolicyManager default entry at `HKLM\SOFTWARE\Microsoft\PolicyManager\default\Security\RecoveryEnvironmentAuthentication` carries `RegKeyPathRedirect = Software\Policies\Microsoft\WinRE` and `RegValueNameRedirect = WinREAuthenticationRequirement`, which means the CSP writes a plain policy registry value and Group Policy can write the same one. I set it both ways.
2. **Disabling the recovery environment closes every entry at once**, including the one no software can stop: interrupting the boot twice. The cost is that Reset, Startup Repair, Safe Mode from the menu and the recovery command prompt stop working for everyone, and a feature update turns it back on during its specialize pass ([REAgentC](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/reagentc-command-line-options)). Rebuild from the baseline is this workspace's recovery path anyway, so I disabled it and scheduled the disable to recur.
3. **The 2026-09-12 Settings lockdown used `hideonly:`**, which Microsoft does not document; the accepted prefixes are `showonly:` and `hide:` ([Settings Page Visibility](https://learn.microsoft.com/en-us/windows/configuration/settings/page-visibility)). Whether Windows honoured it is unknown. I replaced it with a `showonly:` allowlist, which fails closed when Microsoft adds a page.

Beyond that, the AppLocker review found the writable-folder exception list short of what the machine actually has, the 32-bit registry editor not denied, two toolchain paths allowed for languages nobody approved, and the whole family of script and DLL hosts under `%WINDIR%` open to the restricted group.

## What I built

**A third computer policy, `C-WKS-ObiPC-Lockdown`**, created 2026-09-18, linked fifth to `OU=Standard,OU=Workstations`, user side disabled, `Authenticated Users` read only and `OBIPC$` apply, the same filtering as `C-WKS-ObiPC-AppControl`. Registry values only, no template dependency:

| Key under `HKLM` | Value | Effect |
|---|---|---|
| `SOFTWARE\Policies\Microsoft\WinRE` | `WinREAuthenticationRequirement = 1` | Every recovery tool, "Remove everything" included, asks for an administrator account |
| same | `DisableSetup = 1` | The legacy "Allow restore of system to default state" policy, disabled; depth only, Microsoft's own text says it does not gate the recovery menu |
| `SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System` | `ShutdownWithoutLogon = 0` | Power button gone from the sign-in screen, and Shift+Restart with it |
| same | `InactivityTimeoutSecs = 900` | Locks after 15 idle minutes |
| same | `NoConnectedUser = 1` | No Microsoft accounts can be added |
| `SOFTWARE\Policies\Microsoft\Windows\Appx` | `AllowAllTrustedApps = 0`, `AllowDevelopmentWithoutDevLicense = 0` | No sideloaded packages; a signed MSIX is the one install that never needed elevation |
| `SOFTWARE\Policies\Microsoft\Windows\AppInstaller` | `EnableMSAppInstallerProtocol = 0`, `EnableLocalManifestFiles = 0` | Web-initiated and local-manifest App Installer paths closed for everyone; the App Installer app itself is denied to the restricted group in AppLocker instead of machine-wide |
| `SOFTWARE\Policies\Microsoft\Windows\WorkplaceJoin` | `BlockAADWorkplaceJoin = 1` | No user can add a work account or register the device a second time; Microsoft's recommended setting for hybrid-joined machines |
| `SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate` | `SetDisableUXWUAccess = 1` | Windows Update UI removed for all users; patching is Action1's |
| `SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer` | `NoDriveTypeAutoRun = 255`, `NoAutoplayfornonVolume = 1` | AutoPlay off everywhere |
| `SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\Internet Settings` | `ProxySettingsPerUser = 0` | Proxy is machine-wide, so a standard user cannot set one |
| `SOFTWARE\Policies\Microsoft\Windows Defender Security Center\...` | `DisallowExploitProtectionOverride = 1`, `DisableClearTpmButton = 1` | No relaxing of exploit protection, no TPM clear from the Windows Security app |
| `SYSTEM\CurrentControlSet\Control\FileSystem` | `LongPathsEnabled = 1` | The one developer setting the hidden Advanced page carried, set for him |

**`U-WKS-ObiPC-Restricted` extended**, still filtered to `ROL-ObiPC-Restricted`, version 18:

- `SettingsPageVisibility` is now `showonly:` display, night light, graphics, sound, volume mixer, notifications and the four focus pages (hiding any `quietmoments` page hides Notifications, per Microsoft), multitasking, every personalisation page, taskbar, mouse, touchpad, typing, pen, printers, region and language, keyboard, speech, control center, and every accessibility page. Everything else, Recovery, Update, Accounts, Network, Apps, Privacy, About, Power, Storage, Bluetooth, Developers, Sign-in options and the rest, is gone, and Microsoft documents that a hidden page is unreachable by `ms-settings:` URI as well.
- `RestrictCpl = 1` with nine permitted Control Panel items: `Microsoft.Personalization`, `Microsoft.Mouse`, `Microsoft.Keyboard`, `Microsoft.Sound`, `Microsoft.EaseOfAccessCenter`, `Microsoft.RegionAndLanguage`, `Microsoft.ColorManagement`, `Microsoft.NotificationAreaIcons`, `Microsoft.DevicesAndPrinters`. Control Panel and Settings are separate policies with separate universes; both were needed.
- `NoClose = 1`: the power button and Shut Down, Restart, Sleep and Hibernate are removed from Start and from the Ctrl+Alt+Del screen for him. He signs out instead. I chose this over the machine-wide `HidePowerOptions`, which would have taken the power button from me too.
- `HKCU\Software\Policies\Microsoft\MMC\RestrictToPermittedSnapins = 1`: `certmgr.msc`, `taskschd.msc`, `services.msc` and every other snap-in refuse to load, closing the Control Panel policy's known leak.
- Edge `ExtensionInstallBlocklist = *`, matching the Chrome rule that was already there.

**AppLocker policy, second version**, imported into `C-WKS-ObiPC-AppControl` at about 11:10 PM as GPO version 7 with sha256 `4a942f6e79fafca939d6546e3c00d05353393cdb5a7977212f177541ee2c515b`: Exe 56 rules, 44 of them denies; Msi 4; Appx 4; Script 12, still audit only. The second pass below replaced it at 11:35 PM with the third version, which is what [`Configuration/ObiPC-AppLocker.xml`](../../Configuration/ObiPC-AppLocker.xml) now holds. The rest of this section describes what the second version changed relative to 2026-09-12; the third removed the restricted group's eight executable allows and nothing else.

- **Exceptions on the `Everyone` Windows-folder rule grew from 13 to 23**, from a `Get-Acl` sweep of every directory under `C:\Windows` for `Users`, `Authenticated Users`, `Everyone` and `INTERACTIVE` write rights. New: `MachineKeys` (both trees), `spool\SERVERS`, `Tasks_Migrated` (both), `PLA`, `AppLocker` (both, the cache-file alternate-data-stream trick), the whole `debug` tree, and `Panther` and `Logs\PBR`, which the reset left with `Authenticated Users: Modify` all the way down. I also reset those two trees to inherit from `C:\Windows` with `icacls /reset /T`, 226 and 249 objects, so the exception is a second wall rather than the only one.
- **Denies for `ROL-ObiPC-Restricted`, by path with `%SYSTEM32%` covering both bitnesses:** `shutdown.exe`, `SystemReset.exe`, `SystemSettingsAdminFlows.exe` (the modern reset entry point; `SystemReset.exe` is absent on this build), `ReAgentc.exe`, `bcdedit.exe`, `msconfig.exe`, `dism.exe`, `wusa.exe`, `RecoveryDrive.exe`, `recdisc.exe`, `rstrui.exe`, `mshta.exe`, `wscript.exe`, `cscript.exe`, `regsvr32.exe`, `control.exe`, `wbem\WMIC.exe`, `hh.exe`, `forfiles.exe`, `pcalua.exe`, `ie4uinit.exe`, `sdclt.exe`, `bitsadmin.exe`, `certutil.exe`, `ftp.exe`, the whole `%WINDIR%\Microsoft.NET\*` tree (MSBuild inline tasks, InstallUtil, RegAsm, RegSvcs, the compilers), `%WINDIR%\WinSxS\*` and `%WINDIR%\servicing\LCU\*`, because every System32 binary has a copy in both and a path deny on System32 alone is defeated by running the copy. The 32-bit `regedit.exe` joins the two registry-editor denies from before.
- **Thirteen publisher denies** for the same group on the binaries that matter most, generated on the machine with `Get-AppLockerFileInformation` so the product strings are exact: the Windows operating system product for `shutdown`, `SystemSettingsAdminFlows`, `ReAgentc`, `bcdedit`, `msconfig`, `regsvr32`, `control` and `regedit`; Internet Explorer for `mshta`; Windows Script Host for `wscript` and `cscript`; .NET Framework for `MSBuild` and `InstallUtil`. A publisher deny follows the file when it is copied into `C:\Dev`, which a path deny does not.
- **Allow changes:** `.vscode*\*` tightened to `.vscode\*` and `.vscode-insiders\*`, because the wildcard let any directory starting with `.vscode` run code; the Rust and Go rules removed, since neither is an approved toolchain; `npm-cache` under both profile roots added, because `npx` unpacks and runs from there; Msi gains an explicit `Deny *` for the restricted group; Appx gains a deny for `Microsoft.DesktopAppInstaller` from `CN=Microsoft Corporation` for the restricted group, so `winget` cannot install a signed package for him while the Appx allow stays broad enough to keep the Start menu alive. Every rule now carries a description saying why it exists.
- **Deliberately not denied:** `rundll32.exe`, which the shell calls constantly and would fail in confusing ways; `curl.exe`, a daily tool for a web developer; `msiexec.exe`, which would break self-repair of installed products and is queued for a week of audit first; `cmd.exe`, `powershell.exe`, `node`, `python`, VS Code, which are the point of the machine.

**A recovery lockdown task**, [`Scripts/Enforce-ObiPCRecoveryLockdown.ps1`](../../Scripts/Enforce-ObiPCRecoveryLockdown.ps1), sha256 `1d4e5b3eb9890d2561782bb3e9ad406a4485ce914bc0a71cfb45031b12e27b83` on both the repo copy and `C:\ProgramData\ObiPC-Lockdown\`, a folder locked to SYSTEM and Administrators. The scheduled task `ObiPC Recovery Lockdown` runs it as SYSTEM one minute after every start and daily at 3:00 AM. Each tick: `reagentc /info`, `reagentc /disable` if enabled, then the `RecoveryEnvironmentAuthentication` policy through the MDM bridge class `MDM_Policy_Config01_Security02`, then a readback line to `recovery.log`. Two traps: the bridge refuses any caller but SYSTEM, and the property is a signed integer, so `[uint32] 1` fails with *Type mismatch for property* and `[int] 1` succeeds; the first tick at 11:11:57 PM disabled the recovery environment and failed on the type, the second at 11:13:24 PM created the instance. The `Panther` and `PBR` exceptions above matter here too: the script lives outside `%WINDIR%` on purpose.

**On the machine itself:** `sc.exe config appidsvc start= auto`, so the Application Identity service is `Automatic` rather than the trigger-started `Manual` the rebuild left it at. Group Policy cannot set this on Windows 10 and later because the service is protected, and the 2026-09-12 record's claim that the AppControl policy did so was wrong: the policy report carries no such value.

## Second pass: Action1 becomes the only install path

Your requirement, stated after the first pass: he cannot get software onto the machine by any route other than an Action1 deployment, updates and the machine's core functions keep working, display personalisation stays, the graphics drivers keep working, and none of this lands on any other account. Three things changed.

**The developer carve-out is closed.** The 2026-09-12 design allowed `ROL-ObiPC-Restricted` to run executables from `C:\Dev`, the VS Code extension directories, the npm and npx paths, the pip user scripts and a per-user Python install, and the record called it "a deliberate hole" against the person at the keyboard. A downloaded program copied into any of those directories runs, which is exactly the bypass you asked me to remove. **Third version of the policy**, sha256 `74384686b8c9e9361a8b948f8f912775678ff8fef2d730b624eec8910a327949`, matched on `HQ-DC01` and imported at 11:35 PM as GPO version 8: all eight restricted-group allow rules removed from the Exe collection, so that group now has **no allow rule of its own anywhere for executables**. What runs for him is what the `Everyone` rules cover, `%WINDIR%` and both Program Files trees, which is where Action1 installs. The Script collection keeps the same eight paths, so npm's `.cmd` shims and pip's launchers stay usable when that collection is enforced; they only ever start `node.exe` or `python.exe` from Program Files. What he loses: a compiled binary of his own, a native `.exe` inside a `node_modules` tree, a `pip --user` launcher, and a VS Code extension that ships its own executable. Each of those is now a request to you, answered by an Action1 deployment or a publisher rule.

**Browser downloads of executables and installers are blocked** for his account: `DownloadRestrictions = 2` for Chrome and Edge in `U-WKS-ObiPC-Restricted`, which blocks dangerous and potentially dangerous file types at download time while leaving documents, archives and source files alone. AppLocker already stops anything he does download from running; this removes the file before it lands. The value `3` blocks every download, and is one registry value away if you want that.

**Two machine-wide settings from the first pass are withdrawn**, because they would have restricted you and any other account on the machine: the Windows Update UI removal (`SetDisableUXWUAccess`) and the Microsoft-account block (`NoConnectedUser`). Both were removed from `C-WKS-ObiPC-Lockdown` (now version 19) and the policy refresh removed both values from the machine. His account cannot reach either surface anyway: the Update, Accounts and Your info pages are outside the `showonly:` list. The remaining computer-side settings stay because they are the incident controls or are invisible in ordinary use: the recovery environment, the recovery authentication requirement, the sign-in screen power button, sideloading and App Installer protocol, workplace join, AutoPlay, the machine-wide proxy, the two Windows Security overrides, the 15-minute lock, and long paths. Any other account on `ObiPC` gets a normal Windows with a normal Start menu, Settings, Control Panel, power menu and Windows Update, and members of `ROL-ObiPC-Unrestricted` and local administrators run anything: `Test-AppLockerPolicy` returns `Allowed`, *Unrestricted users: all files*, for the same probe that is denied to him.

**Graphics drivers were checked, not assumed.** The machine carries an NVIDIA GeForce RTX 3070 and the AMD integrated graphics. Every NVIDIA and AMD service runs as `LocalSystem`, which AppLocker does not evaluate, from `C:\Windows\System32\DriverStore` or `C:\Program Files\NVIDIA Corporation`, both inside the `Everyone` allows; the NVIDIA App and its self-update task run from Program Files and test `Allowed`; the AMD Radeon Software control panel is a signed packaged app from AMD's own publisher, allowed by the broad Appx rule, which is one reason that rule was left broad. Driver installation itself needs an administrator and was never his; it is yours, through Action1 or a sign-in.

Verification of the second pass, at 11:35 PM: effective policy `Exe Enabled 48`, `Msi 4`, `Appx 4`, `Script AuditOnly 12`, AppLocker event 8001 at 11:35:54 PM; a copy of `notepad.exe` placed at `C:\Dev\probe\downloaded-app.exe` and at `C:\Users\Public\downloaded-app.exe` returns `DeniedByDefault` for the restricted group's SID and `Allowed` for the unrestricted group's; both probe files removed afterwards; `NoConnectedUser` and `SetDisableUXWUAccess` absent from the registry; `shutdownwithoutlogon` still `0`.

## Verification, from the live machine at 11:14 PM

| Check | Result |
|---|---|
| `gpupdate /force /target:computer` | *Computer Policy update has completed successfully*; `gpresult` lists `C-WKS-ObiPC-Lockdown` fourth of six applied |
| `reagentc /info` | `Windows RE status: Disabled` |
| `HKLM\SOFTWARE\Policies\Microsoft\WinRE` | `WinREAuthenticationRequirement = 1`, `DisableSetup = 1` |
| `PolicyManager\current\device\Security` | `RecoveryEnvironmentAuthentication_ProviderSet = 1` |
| `Policies\System` | `shutdownwithoutlogon = 0`, `InactivityTimeoutSecs = 900`, `NoConnectedUser = 1` (withdrawn in the second pass), `ConsentPromptBehaviorUser = 1` unchanged |
| Appx, AppInstaller, WorkplaceJoin, WindowsUpdate, Explorer, Internet Settings, Security Center, FileSystem | Every value as in the table above |
| Effective AppLocker policy | `Exe Enabled 56 (44 deny)`, `Msi Enabled 4`, `Appx Enabled 4`, `Script AuditOnly 12`; 23 exceptions on the Windows-folder rule; event 8001 at 11:14:42 PM. Superseded by the second pass: `Exe Enabled 48` from 11:35 PM |
| `Test-AppLockerPolicy`, restricted SID, effective policy | `Denied` for `shutdown.exe` (path rule), `SystemSettingsAdminFlows.exe`, `mshta.exe`, `regsvr32.exe`, `MSBuild.exe` and `SysWOW64\regedit.exe` (publisher rules), `wscript.exe`, `control.exe`, `regedit.exe`, `certutil.exe` (path rules); `Denied` for the `WinSxS` copy of `shutdown.exe` by the WinSxS rule |
| `Test-AppLockerPolicy`, unrestricted SID, `shutdown.exe` | `Allowed`, *Unrestricted users: all files* |
| `AppIDSvc` | `Running`, `Automatic` |
| `ObiPC Recovery Lockdown` task | `Ready`, last result 0, two triggers (`At system start up`, `Daily 3:00:00 AM`), `Run As User: SYSTEM`; third tick at 11:14:54 PM read back `WinRE=Disabled`, `_ProviderSet=1`, `WinREAuthenticationRequirement=1` |
| Safe Mode service list | `SafeBoot\Minimal` and `SafeBoot\Network` carry no `AppIDSvc`, so AppLocker would not enforce in Safe Mode; with the recovery environment off and `bcdedit` and `msconfig` needing elevation, a standard user has no route there |
| Optional features | No WSL, Virtual Machine Platform or Windows Sandbox enabled |

One caveat on the AppLocker test: `Test-AppLockerPolicy -User <SID>` matches only rules that name that SID, so it reports `DeniedByDefault` for `cmd.exe`, Chrome and VS Code, which the `Everyone` rules allow on the live machine, proven on his session on 2026-09-12. The test is meaningful for the denies, which is what it was for.

## Costs I accepted

- **No recovery environment for me either.** An unbootable `ObiPC` is a rebuild, which it was anyway. To use Reset or Startup Repair deliberately: `reagentc /enable`, do the work, and the next tick turns it off again.
- **He cannot restart, shut down or sleep the machine from any menu.** The power plan still sleeps it, and I can restart it over SSH or MeshCentral. Reversible by removing `NoClose`.
- **The `showonly:` list may hide a page he needs.** That is the fail-closed direction, and the fix is one identifier added to the list.
- **Control Panel applets are gone for him** even for the nine names permitted, because `control.exe` itself is denied; the Control Panel window inside Explorer still shows those nine.
- **`certutil.exe` is denied.** Lift it if he ever does certificate work.
- **The `WinSxS` and `servicing\LCU` denies** are broader than anything Microsoft recommends. Nothing in a user's session should launch from either tree, but if something does, the AppLocker 8004 event will name it.
- **The developer carve-out is gone.** He runs what Action1 and Windows put under Program Files and Windows, and nothing else. Node and Python scripts still run under their interpreters; anything that needs its own executable is a deployment request. This reverses the 2026-09-12 decision that allowed `C:\Dev` and the toolchain paths, by your instruction.

## Follow-up on 2026-09-19: the Microsoft Store

Closing the developer carve-out left one install path open that I named but did not close: the Microsoft Store. You asked for it, so it is shut.

The Store installs an application into the signed-in user's profile with no elevation and no administrator involved, which is the same property that made `C:\Dev` worth closing. The obvious control does not work here. "Turn off the Store application" is ignored by design on Windows 11 Pro, which Microsoft records in KB3135657, so the policy exists in the editor and does nothing on this machine. AppLocker packaged-app rules do work on Pro, and the App Installer deny from the day before already proved it.

I read the packages on the machine first rather than guessing their identifiers. All of them report the same publisher, `CN=Microsoft Corporation, O=Microsoft Corporation, L=Redmond, S=Washington, C=US`, and these product names:

| Package | Version on ObiPC | Why it is a download path |
|---|---|---|
| `Microsoft.WindowsStore` | 22608.1401.3.0 | The Store itself |
| `Microsoft.StorePurchaseApp` | 22607.1401.4.0 | The acquisition flow behind it; leaving it would leave half the path open |
| `Microsoft.GamingApp` | 2608.1001.17.0 | The Xbox app installs games from the Store without opening the Store |
| `Microsoft.DesktopAppInstaller` | 1.29.290.0 | Already denied on 2026-09-18 |

Three new deny rules, scoped to the restricted group and nobody else, take the packaged-app collection from four rules to seven. I left `Microsoft.Xbox.TCUI`, `Microsoft.XboxGamingOverlay` and `Microsoft.XboxIdentityProvider` alone: they are sign-in dialogs, the Game Bar and an authentication provider, and none of them installs anything.

The web storefront is closed by the same rules. Choosing Get on a page under `apps.microsoft.com` hands off to the `ms-windows-store:` protocol, which launches the package that is now denied. Downloading an `.appx` or `.msix` directly is already covered twice over, by the browser download restriction and by the App Installer deny.

Store-delivered updates for apps he already has should keep working, because the deployment service that installs them runs as `LocalSystem` and AppLocker does not evaluate `LocalSystem`. That is the design, not an observation, and it is in the open list below.

### Verification

| Check | Result |
|---|---|
| Policy version | `C-WKS-ObiPC-AppControl` moved from 8 to 9 on import |
| File on the controller | SHA-256 matched the file in this repository, `72bfe5d9…8699b4` |
| Effective policy on `ObiPC` after a computer refresh | Packaged-app collection `Enabled`, seven rules, the four denies naming the restricted group |
| Deployed rule content | Publisher and product strings on the machine match what the packages themselves report, character for character, with an unbounded version range |
| Control | `regedit.exe` tests `Denied` for the restricted group against the same policy file, so the file and the cmdlet both work |

A tooling note worth keeping: `Test-AppLockerPolicy` cannot evaluate a packaged app. Piping `Get-AppLockerFileInformation` for an `.appx` into it fails with `Cannot find path`, because the cmdlet binds the object as a file system path. The executable control above is how I showed the policy itself is sound. Functional proof for the Store denies needs his session, which is already on the open list.

## Open

- **User-side verification.** Settings allowlist, Control Panel allowlist, `NoClose`, MMC restriction, Edge blocklist: all take effect at `IK-user`'s next sign-in, and I have not seen his session since the rebuild. Check `gpresult /user` and the AppLocker 8004 events after his first day.
- **What Shift+Restart shows now.** With the recovery environment unmapped the menu is degraded or absent; Microsoft does not document which. Nothing in it can launch a reset, but I have not watched it.
- **BitLocker, now TPM+PIN.** The recovery environment reads a plaintext disk. A TPM-only protector would not have stopped this reset; Microsoft lists only TPM+PIN and password protectors as forcing the recovery key first. Recorded as the recommended baseline in the [platform TODO](../TODO.md).
- **Script collection enforcement** after a week of 8003 audit, with `npm-cache` now allowed ahead of it; then `msiexec.exe` after its own audit; `rundll32.exe` only as a standalone change with a test pass.
- **Watch the 8004 events from his first week** for a legitimate tool the closed carve-out now blocks, and deploy it through Action1 or add a publisher rule rather than reopening a path.
- **Appx narrowing** to Microsoft publishers, after an inventory of installed packages, as a separate change with a shell test. The Store, purchase app and Xbox app are denied as of 2026-09-19; the broad `Everyone` allow is still there.
- **Confirm the Store denies on his session** and confirm that Store-delivered updates for apps he already has still arrive. Both need him signed in. The packaged-app block events are 8022 in `Microsoft-Windows-AppLocker/Packaged app-Execution`.
- **After every feature update**, confirm the task turned the recovery environment back off: `recovery.log` shows it.
- Unchanged from before: Git, Node.js and Python from Action1; the OneDrive path; RSAT.
