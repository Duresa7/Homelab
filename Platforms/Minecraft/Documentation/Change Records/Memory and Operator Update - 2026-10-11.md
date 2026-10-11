# Memory increase and operator request

**Created:** 2026-10-11  
**Last updated:** 2026-10-11

I increased `alpha-prod-01` from 6 GiB to 8 GiB maximum and minimum RAM, then increased Minecraft's maximum Java heap from 2 GiB to 4 GiB and its container limit from 3 GiB to 5 GiB. The combined memory/swap limit is also 5 GiB. I retained six vCPUs, the 1 GiB initial heap, Minecraft 26.3 and the existing world. View distance and simulation distance remain 10; I did not implement the distance trial from the [capacity check](../Capacity%20Research%20-%202026-10-11.md).

## Implementation

Before the change I checked Purple's memory: 6240 MiB available, no swap use, and `app-01` still stopped. Alpha had 3835 MiB available. I did not retain full transcripts of these preliminary checks.

At 5:54:26 PM Eastern I [saved the revised definition](../../Evidence/Memory%20and%20Operator%20Update%20-%202026-10-11/Dockhand%20Save.json) in Dockhand environment 6 without deploying it, then [stopped Minecraft cleanly](../../Evidence/Memory%20and%20Operator%20Update%20-%202026-10-11/Minecraft%20Shutdown.json) with exit code 0. I shut down VM 401, set `memory: 8192` and `balloon: 8192`, and started it again. The [VM change transcript](../../Evidence/Memory%20and%20Operator%20Update%20-%202026-10-11/VM%20Memory%20Change.json) shows it running at 5:54:51 PM. This restart briefly interrupted TeamSpeak and the shared Playit agent.

I [deployed the saved Minecraft stack](../../Evidence/Memory%20and%20Operator%20Update%20-%202026-10-11/Dockhand%20Deployment.json) through Dockhand at 5:55:28 PM Eastern, with no image pull or build. The container was recreated using the existing image. I created no snapshot, backup, credential staging file or persistent management-session file.

## Verification

- The [Proxmox readback](../../Evidence/Memory%20and%20Operator%20Update%20-%202026-10-11/Proxmox%20Verification.json) shows 8192 MiB current memory and balloon minimum, six vCPUs, and no pending memory change. Purple reported 7499 MiB available after the restart; this is a lightly loaded sample, not a worst-case reserve.
- The [guest and service check](../../Evidence/Memory%20and%20Operator%20Update%20-%202026-10-11/VM%20and%20Service%20Verification.json) shows 7879 MiB usable memory, no swap use, a healthy Minecraft container, live `-Xmx4G -Xms1G` JVM flags, and 5,368,709,120-byte container memory and combined memory/swap limits. The world retained inode 2621621 and `level.dat`; startup completed at 5:55:39 PM without generating a replacement world.
- My [initial JVM check](../../Evidence/Memory%20and%20Operator%20Update%20-%202026-10-11/Initial%20JVM%20Check.json) failed because `docker top` requires a PID column. I repeated it with `pid,args`, which produced the verified heap flags above.
- The first TeamSpeak collector sample overlapped startup and showed failed probes. At 5:56:30 PM Eastern the [fresh sample](../../Evidence/Memory%20and%20Operator%20Update%20-%202026-10-11/TeamSpeak%20Final%20Verification.json), one second old, reported local voice, public voice, DNS SRV and ServerQuery up for both servers. Playit had restarted once during boot and was running. I redacted private relay labels from the earlier saved evidence and filtered them before output in the final check.
- The [LAN](../../Evidence/Memory%20and%20Operator%20Update%20-%202026-10-11/LAN%20Status.json) and [public SRV](../../Evidence/Memory%20and%20Operator%20Update%20-%202026-10-11/Public%20SRV%20Status.json) probes returned Minecraft 26.3, protocol 777, zero connected players and a 20-player maximum at 5:56 PM Eastern, in 5.2 ms and 163.2 ms respectively. I did not test an authenticated player join.
- The [Dockhand readback](../../Evidence/Memory%20and%20Operator%20Update%20-%202026-10-11/Dockhand%20Verification.json) matches the repository Compose reference. The [runtime Compose validation](../../Evidence/Memory%20and%20Operator%20Update%20-%202026-10-11/Runtime%20Compose%20Verification.json) passed, with the same SHA-256 digest as the saved definition.

## Operator request

I set out to make `mobivalgod` a server operator, but no such Java profile exists. Both `api.mojang.com/users/profiles/minecraft/mobivalgod` and `api.minecraftservices.com/minecraft/profile/lookup/name/mobivalgod` returned HTTP 404. The server's two-entry player cache contains no matching name, and `ops.json` has zero entries. I did not retain separate captures of these lookups. Nobody holds operator permissions until I confirm the exact Java profile name, which stays open in the root [TODO](../../../../TODO.md).

The MOTD remains `AlphaSec United Minecraft`. It appears in the multiplayer server list, as described by the [Minecraft server setup documentation](https://help.minecraft.net/hc/en-us/articles/360058525452). I did not add a custom join message.
