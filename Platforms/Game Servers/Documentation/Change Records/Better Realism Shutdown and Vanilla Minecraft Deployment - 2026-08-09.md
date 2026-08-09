# Better Realism Shutdown and Vanilla Minecraft Deployment

**Created:** 2026-08-09  
**Last updated:** 2026-08-09

**Implemented:** 2026-08-09  
**Owner:** Platforms / Game Servers  
**Host:** `game-01`, LXC 123 on `green-server`, `192.168.80.30`  
**Status:** Complete. Better Realism is stopped and retained, and Vanilla Minecraft 26.2 is running on the existing public path.

## Scope

I shut down Better Realism without deleting its Pelican record, container, volume, or world. I then deployed a separate unmodified Minecraft Java Edition server at the stable release that Mojang marked current on 2026-08-09.

[Mojang's version manifest](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json) reported `26.2` as `latest.release`. The 26.2 metadata requires Java 25 and names the official server JAR whose SHA-1 is `823e2250d24b3ddac457a60c92a6a941943fcd6a`. I pinned the Pelican variable to `26.2` instead of leaving it at `latest`, so a later reinstall cannot silently advance this server.

I made no backup or snapshot. That follows the standing no-backup rule, but it means both retained worlds depend on the one `game-01` root volume.

## Better Realism shutdown and retention

I stopped Pelican server ID 2 through Wings. The process exited with code 0 after saving all three dimensions. I did not use `docker stop`, because Wings crash recovery can restart a container stopped outside Pelican.

The retained server is:

| Item | Final state |
| --- | --- |
| Name | Better Realism MC 7.2.0 |
| Pelican server ID | 2 |
| UUID and volume | `adf6c266-8f78-4505-9382-0b972d43f660`; volume present at 363 MiB |
| Runtime | Minecraft 1.21.1, Fabric 0.19.3, Java 21 |
| State | Stopped, container `exited`, exit code 0 |
| Allocation | ID 2, `192.168.80.30:25566`; not on the public relay |
| Limits | 1024 MiB memory, 100 percent CPU, 30720 MiB disk, no swap |
| Startup | `java -Xms4G -Xmx8G ... -jar server.jar` |

Pelican counts assigned limits even when a server is stopped. I reduced the dormant memory and CPU limits so the node could admit Vanilla, while retaining the 30 GiB disk allowance and every server file. The parked server cannot boot with a 4 GiB initial heap inside its current 1 GiB memory allowance. Reactivating it requires stopping or shrinking Vanilla and restoring appropriate Better Realism limits first.

## Vanilla deployment

I imported Pelican's official [`Vanilla Minecraft` egg](https://github.com/pelican-eggs/minecraft/blob/main/java/vanilla/egg-vanilla-minecraft.yaml) from its `main` branch. It became egg ID 3 alongside the existing NeoForge and Fabric eggs.

I created this server:

| Item | Final state |
| --- | --- |
| Name | Vanilla Minecraft 26.2 |
| Pelican server ID | 3 |
| UUID and volume | `291851da-5a7e-465a-b3b3-8c5c5b936ef3`; volume present at 126 MiB after first boot |
| Egg and variables | Vanilla Minecraft; `SERVER_JARFILE=server.jar`, `VANILLA_VERSION=26.2` |
| Runtime | Minecraft Java Edition 26.2 on Temurin 25.0.3 |
| Image | `ghcr.io/pelican-eggs/yolks:java_25` |
| Startup | `java -Xms128M -XX:MaxRAMPercentage=95.0 -jar {{SERVER_JARFILE}}` |
| Allocation | ID 1, `192.168.80.30:25565` |
| Limits | 8192 MiB memory, 400 percent CPU, 20480 MiB disk, no swap |
| State | Running and public |

The installed `server.jar` matched Mojang's official 26.2 SHA-1. I accepted the EULA in `eula.txt`; the generated properties leave `server-ip` blank, set `server-port=25565`, retain `online-mode=true`, allow 20 players, and leave the whitelist off.

The node now assigns 9216 of 10240 MiB memory, 500 of 600 percent CPU, and all 51200 MiB of its Pelican disk quota. The LXC itself reported 6.0 GiB used and 69 GiB available on its 79 GiB root filesystem after deployment.

## Public path

I kept Vanilla on `192.168.80.30:25565`, so no Playit, relay, firewall, or DNS change was needed:

`minecraft.alphasecunited.com` -> DNS-only Minecraft SRV/CNAME -> Playit -> `127.0.0.1:25565` -> `minecraft-playit-relay.service` -> `192.168.80.30:25565`

The public relay points only at Vanilla. Better Realism remains assigned to 25566 and is not public.

## Verification

| Check | Result |
| --- | --- |
| Better Realism shutdown | Container exited with code 0 after complete world saves; remained stopped after the Vanilla restart test |
| Better Realism retention | Pelican server ID 2, UUID, 363 MiB volume, and `world/` remained present |
| Official Vanilla JAR | SHA-1 `823e2250d24b3ddac457a60c92a6a941943fcd6a`, matching Mojang's 26.2 metadata |
| First Vanilla boot | `Starting minecraft server version 26.2`; `Done (4.934s)!` |
| Persistence test | Pelican restart completed and the existing world reached `Done (0.257s)!` |
| Direct status | `192.168.80.30:25565` returned 26.2, protocol 776, 0 of 20 players, `A Minecraft Server` |
| Public status after restart | `minecraft.alphasecunited.com` through SRV returned 26.2, protocol 776, 0 of 20 players in 117.7 ms |
| Authentication and EULA | `online-mode=true`; `eula=true` |
| Services | `wings`, `playit`, `minecraft-playit-relay`, and `docker` enabled and active |
| Guest health | LXC running, 0 MiB swap used, root filesystem 8 percent used |
| Containers | Vanilla running on Java 25; Better Realism exited with code 0; panel and cAdvisor healthy |

I retained no separate evidence folder or terminal transcript. The table records the live post-change results I observed through Pelican, Wings, Docker, the guest filesystem, and the direct and SRV-aware status probes.

## Remaining state

- No backup or snapshot exists for either world.
- Pelican has 1024 MiB memory and 100 percent CPU unassigned, but no unassigned disk quota. A third server requires disk reallocation or a node capacity change.
- Better Realism is preserved as a stopped rollback workload, not a server that can be started under its parked 1 GiB limit.
- `VANILLA_VERSION=26.2` is installer state. Upgrading requires changing the exact version and reinstalling deliberately; a normal restart does not download a newer Minecraft release.
