# ObiPC Installed Games Review

**Created:** 2026-09-28  
**Last updated:** 2026-09-28

At about 4:40 PM EDT on 2026-09-28 I checked which games are installed on ObiPC and how they got there. `IK-user` was signed in at the time. I read the machine-wide and per-user uninstall entries, the Steam library manifests, and the Ubisoft, Epic, Riot and Xbox locations, and checked both drives. I made no live changes.

## What is installed

| Game | Source | Size | Game folder created | Last played |
|---|---|---|---|---|
| Tom Clancy's Rainbow Six Siege | Steam | 48.4 GB | 2026-09-20 7:19 PM | 2026-09-22 4:10 PM |
| Counter-Strike 2 | Steam | 68.9 GB | 2026-09-20 7:47 PM | 2026-09-21 4:10 PM |
| Rocket League | Steam | 40.7 GB | 2026-09-21 3:30 PM | 2026-09-21 5:46 PM |
| Cyberpunk 2077 | Steam | 85 GB | 2026-09-22 8:14 PM | 2026-09-22 9:05 PM |
| Roblox Player | App Portal, per user | not measured | installed 2026-09-20 7:17:07 PM; the uninstall entry reads 2026-09-22, which is its current version | not recorded |

The Last played times come from the Steam manifests. The account was disabled from 2026-09-23 to 4:19 PM on 2026-09-28, which matches no play after 2026-09-22.

Rainbow Six Siege brought in `Ubisoft Connect` and `Ubisoft Anti-Cheat`, both machine-wide and both installed with it. Nothing is installed from Epic, Riot or the Xbox app. There is no `C:\Riot Games` or `C:\ProgramData\Riot Games\Metadata` folder, so VALORANT, which is in the App Portal catalog, was never installed. `D:` holds only the recycle bin and `System Volume Information`. Games use 243 GB of the 335.2 GB used on `C:`.

Steam itself came from App Portal. I approved it and installed it on 2026-09-20 at 7:17:38 PM ([record](../../Platforms/App%20Portal/Documentation/Change%20Records/Version%200.6.0,%20the%20Agent%20and%20the%20Game%20Catalog%20-%202026-09-20.md)), and the Steam folder is timestamped 7:17:37 PM. **I did not approve any of the four Steam games.** He installed them through the Steam client, starting two minutes after it landed.

The non-game software he has is Spotify, Discord, Snapchat as a Chrome app, VLC and Firefox. None of it is covered here.

## Steam's folder bypasses the allowlist

`C:\Program Files (x86)\Steam` grants `BUILTIN\Users` Full Control, set explicitly, not inherited. It is the only first-level folder under either Program Files tree that grants write access to a non-administrator group. The AppLocker rule `Everyone: Program Files` allows `%PROGRAMFILES%\*` with no exceptions, and `steam.exe` tests `Allowed` for `S-1-1-0` by that rule.

Taken together, any executable that `IK-user` copies into the Steam folder will run. This is the same shape as the `C:\Dev` carve-out that the [2026-09-18 lockdown](../../Platforms/Active%20Directory/Documentation/Change%20Records/ObiPC%20Recovery%20and%20Settings%20Lockdown%20-%202026-09-18.md) closed. It is also why the [2026-09-20 publisher allows](../../Platforms/Active%20Directory/Documentation/Change%20Records/ObiPC%20Publisher%20Allows%20-%202026-09-20.md) said Steam needed no rule. Steam grants the permission itself so that its client can update without elevation.

I found no sign that the gap has been used:

- The Steam folder holds 26 executables and scripts outside `steamapps\common`, and all 26 are validly signed by Valve. He owns 25 of them, which is what a client updating itself in his session looks like.
- `steamapps\common` holds one folder per manifest, plus `Steam Controller Configs`, which Steam creates itself. The executables at each game's root are validly signed by CD PROJEKT S.A., Ubisoft Entertainment Inc. and BattlEye Innovations e.K.

I did not check every file inside the game folders, and I did not check for anything that was run and then deleted. The `Steam Client Service` runs as `LocalSystem` and was `Stopped` with Manual start at the time.

## Follow-up: the four Steam games removed

At about 4:44 PM I removed Counter-Strike 2, Cyberpunk 2077, Rocket League and Rainbow Six Siege. I did not block them, so he can install them again through Steam. Steam and its games were not running. I did the removal from a one-off `SYSTEM` task, because deleting 243 GB could outlast an SSH call. For each of the app IDs 730, 1091500, 252950 and 359550 the task deleted:

- the game folder under `steamapps\common`
- its `shadercache` folder, and for 730 its `temp` folder
- `appmanifest_<id>.acf`
- every `Steam App <id>` uninstall key in either registry view. Rocket League had two, one of them with no display name.

Afterwards, Steam's library holds only the `Steamworks Common Redistributables` manifest. `common` holds only `Steam Controller Configs` and `Steamworks Shared`, and `shadercache` is empty. None of the four names appear in the uninstall entries. Free space on `C:` went from 595.3 GB to 847.9 GB. The task, its script and its log were removed, and all three read back absent.

I left Steam, `Ubisoft Connect` and `Ubisoft Anti-Cheat` installed, along with the saved games in his profile and Steam's Controller Configs. One empty uninstall key, `Steam App 3240220`, was there before the removal. It has no manifest and no game folder, and I left it. I did not check what it belonged to.

## Follow-up: Steam, Ubisoft and the GTA V remnant removed

At 4:51 PM I removed Steam, Ubisoft Connect and Ubisoft Anti-Cheat. I also removed what was left of app 3240220, which Steam's store page names **Grand Theft Auto V Enhanced**. Its uninstall key had no values. The only other traces were a `Rockstar Games\Launcher\stub.log` in his profile from 2026-09-21 3:30 PM and `HKLM\SOFTWARE\WOW6432Node\Rockstar Games`, whose subkeys were `GTA V Enhanced`, `Steam`, `Steam\Launcher` and `Steam\SDK`. It never had game files.

I ran none of the vendor uninstallers. Steam and Ubisoft both ship NSIS uninstallers, and I could not rule out a silent-mode restart, which he had to be spared mid-session. Instead a one-off `SYSTEM` task did the following:

- **Services:** stopped and deleted `UpcElevationService`, `sen_service` and `Steam Client Service`, all three already `Stopped`, with `sc.exe delete` exit 0.
- **Scheduled task:** deleted `\Ubisoft\Ubisoft Connect Background Update` and its folder.
- **Firewall:** deleted the 26 rules whose program was inside the Steam or Ubisoft folders: Steam, Steam Web Helper and the four games. The 12 `Microsoft Teams` rules that a looser match had caught in the inventory were left alone.
- **Folders:** deleted both Ubisoft trees and `C:\ProgramData\Ubisoft`; `C:\Program Files (x86)\Steam` and `Common Files\Steam`; the Steam Start menu folders, machine and his; and his `Ubisoft Game Launcher`, `Steam` and `Rockstar Games` folders under `AppData\Local`.
- **Shortcuts:** deleted the Public desktop `Steam.lnk` and the four game shortcuts on his desktop.
- **Registry:** deleted the `Uplay`, `Steam`, `Ubisoft-Sentinel` and `Steam App 3240220` uninstall keys; `Valve` and `Ubisoft` in both registry views; the `steam` and `uplay` URL handlers; `Rockstar Games`; and his own `Software\Valve`, `Software\Ubisoft` and `Classes\steam`.

Verification at 4:52:20 PM found none of these apps, services, folders, shortcuts, keys, tasks or firewall rules. Free space on `C:` went from 847.85 GB to 850.79 GB. The last boot still read 2026-09-27 5:49:16 PM. None of the three pending-restart markers (`RebootPending`, `RebootRequired`, `PendingFileRenameOperations`) was set. His session was still open, and the pass read 28.0 minutes used. The task, its script, the log and the verification script were all removed.

Removing Steam also removes the user-writable folder described above. Steam is still in the App Portal catalog, and the catalog installs without my approval, so he can bring it and the gap back himself. I did not change the catalog.

## Open

The fix is tracked in the [Active Directory TODO](../../Platforms/Active%20Directory/Documentation/TODO.md). No separate terminal capture was retained.
