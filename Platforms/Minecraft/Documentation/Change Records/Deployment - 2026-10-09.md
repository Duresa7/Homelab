# Deployment

**Created:** 2026-10-09  
**Last updated:** 2026-10-09

**Status:** LAN deployment complete; Playit publication pending.  
**Verification:** 2026-10-09, 1:39 PM Eastern.

I deployed Vanilla Minecraft Java Edition 26.3 as a Docker Compose stack on `alpha-prod-01`, managed through Dockhand. I stopped `app-01` for the time being and added 2 GiB to Alpha's configured memory. CPU and disk allocations are unchanged.

## VM changes

| Setting | Before | Verified after |
|---|---|---|
| app-01, VM 116 | Running, automatic startup enabled | Stopped; `onboot: 0`; existing four vCPUs, 8 GiB maximum / 4 GiB minimum RAM and 64 GiB disk retained |
| alpha-prod-01, VM 401 | Six vCPUs, 4 GiB maximum / 2 GiB minimum RAM, 60 GiB disk | Running; six vCPUs, 6 GiB maximum and minimum RAM, 60 GiB disk; `onboot: 1` |

I found about 41.43 GiB free on Alpha before deployment, so I did not expand its disk. I applied the memory increase through a clean stop/start. A shutdown request did not reach stopped state within its 45-second wait; a delayed `systemctl poweroff` through the QEMU guest agent reached stopped state before I started the VM again. I did not force-stop it.

I initially retained a 4 GiB balloon minimum. That gave the guest less usable memory than its 6 GiB maximum. Disabling ballooning produced a pending device change, so I instead set `balloon: 6144` online. Proxmox then reported both current memory and current balloon minimum at 6144 MiB with no pending memory changes. The guest reported 5863 MiB usable memory after kernel reservations. Purple had 4505 MiB available during the final Proxmox check. Galaxy still holds 12 VMs and six LXCs, with 15 guests running.

I retain the structured [verification export](../../Evidence/Deployment%20-%202026-10-09/Exports/Verification.json), the [initial shutdown and memory-setting transcript](../../Evidence/Deployment%20-%202026-10-09/Logs/Shutdown%20and%20Initial%20RAM%20Setting.json), and the [final VM configuration transcript](../../Evidence/Deployment%20-%202026-10-09/Logs/Final%20VM%20Configuration.json). I did not retain full terminal transcripts for the intervening shutdown recovery or balloon-minimum correction.

## Compose deployment

I saved the stack in Dockhand environment 6 as `minecraft`. The editable definition lives at `/opt/docker/dockhand/stacks/alpha_prod_01/minecraft/compose.yaml` on `docker-main`; the persistent bind mount lives at `/opt/docker/minecraft/data` on `alpha-prod-01`. Hawser stages the runtime Compose file at `/opt/docker/hawser/stacks/minecraft/compose.yaml`. At 1:37 PM Eastern, the [source and deployment-history check](../../Evidence/Deployment%20-%202026-10-09/Logs/Dockhand%20Source%20and%20Deploy%20History.json) confirmed the stack running, run 1388 successful, and the repository [Compose reference](../../Configuration/compose.yaml) byte-identical to the saved file.

I set a 2 GiB maximum Java heap, a 3 GiB container limit and a 3 GiB combined memory/swap limit. The final image is `itzg/minecraft-server:stable-java25`; Minecraft is pinned to 26.3, online authentication is enabled, RCON is disabled, and the player limit is 20. I accepted the Minecraft EULA in the definition. `dockhand.update: "false"` excludes the server from automatic image replacements. The image's [Java tag documentation](https://docker-minecraft-server.readthedocs.io/en/latest/versions/java/) describes the stable Java 25 variant; the running JVM reports Temurin 25.0.4+7.

An early deployment failed with `Failed to up via Hawser: Hawser Edge agent is not connected` while Alpha was restarting. The connection recovered, and Dockhand run 1385 deployed the initial definition at 1:25:40 PM Eastern. Run 1386 made no container change; run 1387 applied the final definition at 1:28:03 PM Eastern. I then forced one replacement through Dockhand to verify persistence. Run 1388 recreated the container successfully at 1:29:01 PM Eastern. The world directory retained inode 2621620 and `level.dat` remained present; the replacement logged `Done (0.237s)!` at 1:29:13 PM Eastern. A protocol probe during startup returned connection refused; the repeated post-start checks succeeded. I did not retain full terminal transcripts for these attempts or the pre-replacement world check; Dockhand retains its deployment history and the export records the final state.

## Verification and cleanup

At 1:31 PM Eastern, the final container was running and healthy with zero restarts. The observed 3,221,225,472-byte memory and combined memory/swap limits match the reference. The LAN and host-loopback status probes returned Minecraft 26.3, protocol 777, zero connected players, a 20-player maximum and `AlphaSec United Minecraft`. The LAN response took 5.2 ms. I repeated the LAN check at 1:32 PM Eastern and received the same version, player limit and MOTD in 5.1 ms. The Mojang server JAR SHA-1 matched `33680f5f2ac32864d6d7cf5e56a705fdb3e05f4c` from the [official release manifest](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json). The [container and world transcript](../../Evidence/Deployment%20-%202026-10-09/Logs/Container%20and%20World%20Verification.json) and [container details and voice reachability transcript](../../Evidence/Deployment%20-%202026-10-09/Logs/Container%20Details%20and%20Voice%20Reachability.json) retain the later checks.

Both TeamSpeak containers, TS3 Manager, the existing Playit agent, the collector, Hawser and cAdvisor were running after the VM restart. The collector reported local voice, public voice, DNS SRV and ServerQuery up for both `ts02` and `ts03`; its file was 59 seconds old. I changed no TeamSpeak or Playit configuration.

Docker Compose validation passed for the repository definition and the runtime definition. My first [runtime check](../../Evidence/Deployment%20-%202026-10-09/Logs/Runtime%20Compose%20Permission%20Check.json) could not read the protected file through the unprivileged SSH session. I repeated the read-only validation inside the existing Hawser container at 1:39 PM Eastern, where it [returned exit code 0](../../Evidence/Deployment%20-%202026-10-09/Logs/Runtime%20Compose%20Validation.json). The container's Compose labels also confirmed the runtime path and `dockhand.update: false`.

I removed the unused initial `itzg/minecraft-server:java25` image after checking that no container referenced it. Alpha then had 40.13 GiB free and 4004 MiB available memory, with all 3175 MiB of host swap free. At 1:34 PM Eastern I also removed the unused initial definition under Dockhand's `stacks/imported/alpha_prod_01/minecraft/` after verifying the current source file's hash and the API's selected path. The [cleanup transcript](../../Evidence/Deployment%20-%202026-10-09/Logs/Obsolete%20Compose%20Source%20Cleanup.json) confirms that the authoritative file remains present. I created no snapshot, backup or credential-bearing deployment file. The temporary Dockhand login cookie file was removed after verification.

## Playit

The [Game 01 retirement record](../../../../Archive/Platforms/Game%20Servers/Documentation/Change%20Records/Game%2001%20Retirement%20-%202026-09-12.md#retained-history) says I retained the external Playit allocation while deleting its local agent and removing the Minecraft CNAME and SRV records. That supports trying to reuse the old allocation, but I have not verified its current state in the Playit account.

The supplied Playit screenshots show the Minecraft tunnel still allocated to an offline agent and the TeamSpeak agent connected. The [Playit client API](https://github.com/playit-cloud/playit-agent/blob/master/packages/api_client/src/api.rs) supports changing a tunnel's assigned agent through `new_agent_id`. I propose assigning the retained Minecraft tunnel to the connected TeamSpeak agent, keeping the existing tunnel allocation, and setting its TCP origin to `127.0.0.1:25565`. The existing agent runs with host networking on Alpha, so it can reach that origin without another container or credential.

Publication waits for the Playit account-side change or the details needed to restore its separate agent. I will verify the public Minecraft protocol response after connecting the tunnel and restore the public DNS names if requested. I added no WAN port forward, tunnel or DNS record during this deployment. Player login has not been tested.
