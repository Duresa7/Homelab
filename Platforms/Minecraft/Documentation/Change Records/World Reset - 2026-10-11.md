# World reset

**Created:** 2026-10-11  
**Last updated:** 2026-10-11

I deleted the active Minecraft world on `alpha-prod-01` and generated a fresh world at 5:13 PM Eastern. This removed the old terrain, dimensions and player progress. I retained Minecraft Java 26.3, Survival mode, Easy difficulty, the 20-player limit and `minecraft.alphasecunited.com`.

## Reset

I checked the live container's bind mount and `server.properties`: `/opt/docker/minecraft/data` maps to `/data`, `level-name=world`, and `level-seed` is empty. The old world occupied 307 MB and its saved `Time` was 791091 ticks. The LAN status probe reported zero connected players. I did not retain full transcripts of these preliminary checks. A noninteractive sudo write-access check failed with `sudo: a password is required`; I used the existing Docker access for the deletion.

At 5:13:20 PM Eastern I stopped `minecraft`. It exited cleanly with code 0. A temporary container using the same local image, with networking disabled, deleted only `/opt/docker/minecraft/data/world`. I verified that the directory was absent and that hashes of all top-level server files were unchanged before restarting Minecraft at 5:13:23 PM. The temporary container removed itself on exit. I created no snapshot or backup. The [reset transcript](../../Evidence/World%20Reset%20-%202026-10-11/Reset.json) records the operation and its checks.

## Verification

My first check ran during startup: `level.dat` did not yet exist and the LAN probe returned `ConnectionRefusedError: [Errno 111] Connection refused`. I retained the [initial world check](../../Evidence/World%20Reset%20-%202026-10-11/Initial%20Startup%20Check.json) and [initial LAN check](../../Evidence/World%20Reset%20-%202026-10-11/Initial%20LAN%20Check.json).

At 5:13:33 PM Eastern the server logged `No existing world data, creating new world`, followed by `Done (2.947s)!` at 5:13:38 PM. At 5:13:47 PM I verified a newly written `level.dat`, saved `Time` of 0, a 2.4 MB world directory and zero files under `world/players`. The container was healthy with zero automatic restarts. The [world verification transcript](../../Evidence/World%20Reset%20-%202026-10-11/World%20Verification.json) also shows both TeamSpeak containers and the shared Playit agent still running with two days of uptime. The metadata probe's legacy seed lookup returned null; I did not extract the generated seed.

At 5:13:48 PM Eastern the [LAN and public SRV probes](../../Evidence/World%20Reset%20-%202026-10-11/LAN%20and%20Public%20Status.json) both returned Minecraft 26.3, protocol 777, zero players, a 20-player maximum and `AlphaSec United Minecraft`. Response times were 5.3 ms on the LAN and 243.6 ms through the public SRV route.

The reset is complete. I did not test an authenticated player join. The previously recorded [custom-hostname server-list ping limitation](DNS%20Publication%20-%202026-10-09.md) remains outside this change.
