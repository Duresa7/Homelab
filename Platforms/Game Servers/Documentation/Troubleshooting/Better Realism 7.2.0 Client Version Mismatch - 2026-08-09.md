# Better Realism 7.2.0 Client Version Mismatch

**Created:** 2026-08-09  
**Last updated:** 2026-08-09

**Investigated:** 2026-08-09  
**Owner:** Platforms / Game Servers  
**Host:** `game-01`, LXC 123 on `green-server`, `192.168.80.30`  
**Status:** Closed without player-side verification after Better Realism was deliberately stopped and retained.

## Symptom

A player reported a version mismatch while trying to join `minecraft.alphasecunited.com`, despite selecting Better Realism 7.2.0.

The player's Lunar Client startup log supplied the missing exact evidence:

```text
Loading Minecraft 26.1.2 with Fabric Loader 0.19.3
Loading 4 mods:
- java 25
- minecraft 26.1.2
Failed to fetch user properties
InvalidCredentialsException: Status: 401
```

## What I checked

The public status probe reached the server through Minecraft SRV discovery and returned Minecraft 1.21.1, protocol 767, zero of 20 players, and the configured `A Minecraft Server` message. `wings.service`, `playit.service`, and `minecraft-playit-relay.service` were active. The game container had been up since its deployment and the host health check was healthy.

The official CurseForge files form a matching pair:

| Role | CurseForge file | Declared runtime |
| --- | --- | --- |
| Client | 8570128, Better Realism 7.2.0 | Minecraft 1.21.1, Fabric 0.19.3, 141 required files |
| Server | 8570131, Better Realism server pack 7.2.0 | Minecraft 1.21.1, Fabric 0.19.3, Fabric Installer 1.1.2, Java 21 |

CurseForge lists both 7.2.0 files under game version 26.1.2 even though their filenames and internal manifests say Minecraft 1.21.1. The internal manifests are the useful values for this deployment.

I downloaded the official server archive again and verified its SHA-256 as `c1fcb51031edb8aa1f30cb0cd7efac18d3e214ac780378d5c9a69222b4a6d733`. The archive and the live server each contained 134 top-level mod files, including the disabled client-only jars. A filename-sorted SHA-256 manifest of those files produced `e4fddf5dfd3f9a403c59c9e07a040e80a1efe5ee513cb6db717a3016c54b42d3` on both sides. The live server therefore has the official 7.2.0 server mod set byte for byte.

The server has online authentication enabled, does not use a whitelist, and allows proxy connections. Its only log began at deployment and contained no join, login, disconnect, incompatibility, mismatch, or handshake event from a player. The only matches were startup recommendations for optional `modmenu` and `patchouli`; neither prevented startup. The client evidence explains why there was no usable Better Realism login to diagnose on the server.

No separate evidence folder was retained. The findings above come from the live status probe, service state, server log, official archives downloaded into temporary storage, and byte-for-byte mod manifest comparison during this investigation.

## Root cause

The player did not launch the Better Realism 7.2.0 client runtime. The Lunar profile `starz-modpack-6` launched Minecraft 26.1.2 and loaded only Fabric Loader, MixinExtras, Java, and Minecraft. The required runtime is Minecraft 1.21.1 with Fabric Loader 0.19.3 and the complete client file set from CurseForge file 8570128. Fabric Loader matched by coincidence; the Minecraft version and mod set did not.

CurseForge's incorrect 26.1.2 game-version tag makes this mistake easy to make, but the profile's own startup line is decisive. A server-side Minecraft, Fabric, or modpack version mismatch is ruled out by the live runtime and file comparison. A relay outage is ruled out by the successful public status handshake.

The client also had an invalid Mojang session. Both the profile property request and Realms request returned HTTP 401. Because the server uses online authentication, this is a second login blocker that must be cleared after fixing the game profile.

The profile also placed a Litematica jar for Minecraft 26.2 in `resourcepacks/` and logged invalid resource-pack metadata. Those are cleanup findings, not the connection failure.

## Corrective action

The player needs to discard or stop using the current Lunar profile and install CurseForge client file 8570128 as a fresh instance. The known-correct baseline is to launch that instance through CurseForge without copying files from `starz-modpack-6`.

Lunar Client can be retained. Its [profile documentation](https://support.lunarclient.com/support/solutions/articles/60001646811-how-to-create-a-lunar-client-profile) supports importing existing CurseForge profiles and modpacks from the filesystem, and its [CurseForge mod-loading documentation](https://www.lunarclient.com/news/how-to-add-curseforge-mods-to-lunar-client) supports Fabric mods on modern Minecraft versions. The safer Lunar path for this pack is:

1. Install CurseForge client file 8570128 as a clean CurseForge instance.
2. In Lunar Client, choose **Create Profile**, then **Import from Filesystem**.
3. Select the clean CurseForge instance rather than migrating `starz-modpack-6`.
4. Confirm that Lunar identifies Minecraft 1.21.1 and Fabric Loader 0.19.3 before launch.
5. Disable **Use Lunar Features** in the imported profile if the pack crashes or a mod is incompatible. Lunar documents that not every third-party mod is compatible with its features.

The imported profile must load the complete 7.2.0 client mod set rather than the four components in the captured log.

The player must also sign out and back into the Microsoft account used by the launcher so it obtains a fresh Minecraft session. The next startup log must no longer contain an HTTP 401 or `InvalidCredentialsException`.

The Minecraft 26.2 Litematica jar should be removed from `resourcepacks/`. Any later Litematica addition belongs in `mods/` and must target Minecraft 1.21.1, but it should stay out of the first clean connection test.

## Verification and closure

The original player-side fix was not verified. A corrected startup log would have needed to say `Loading Minecraft 1.21.1 with Fabric Loader 0.19.3`, load the Better Realism mods rather than four components, show no authentication 401, and end in a successful server login.

I closed this investigation when I deliberately stopped Better Realism later on 2026-08-09. Its server record, container, volume, and world remain intact, but it is no longer the public workload. Vanilla Minecraft 26.2 now answers `minecraft.alphasecunited.com`; the shutdown and replacement are recorded in [Better Realism Shutdown and Vanilla Minecraft Deployment - 2026-08-09](../Change%20Records/Better%20Realism%20Shutdown%20and%20Vanilla%20Minecraft%20Deployment%20-%202026-08-09.md).

No server configuration was changed during this investigation.
