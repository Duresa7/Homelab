# Game Servers

**Created:** 2026-08-07  
**Last updated:** 2026-08-09

I host my own game servers on `game-01`, an unprivileged LXC on `green-server`. Pelican Panel manages them through a web UI, and its Wings daemon runs each game server in its own Docker container with a memory, CPU and disk limit taken from the panel.

The current public workload is Vanilla Minecraft Java Edition 26.2 on Java 25. Better Realism 7.2.0 remains in Pelican as a stopped, retained server with its world intact.

**Owner:** Platforms / Game Servers

## Layout

- [Configuration/](Configuration/) holds the panel Compose file, a redacted Wings configuration, and the loopback relay unit used by Playit.
- [Tests/](Tests/) holds the Minecraft status probe used for direct and SRV-based checks.
- [Documentation/Deployment.md](Documentation/Deployment.md) preserves the original platform build and first workload.
- [Better Realism MC and Playit Publication - 2026-08-09](Documentation/Change%20Records/Better%20Realism%20MC%20and%20Playit%20Publication%20-%202026-08-09.md) records the destructive workload replacement and public game path.
- [Better Realism Shutdown and Vanilla Minecraft Deployment - 2026-08-09](Documentation/Change%20Records/Better%20Realism%20Shutdown%20and%20Vanilla%20Minecraft%20Deployment%20-%202026-08-09.md) records the retained shutdown, capacity rebalance, and current Vanilla server.

The guest itself belongs to Galaxy, not here. Its creation record is [Galaxy Game-01 LXC Deployment - 2026-08-07](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Game-01%20LXC%20Deployment%20-%202026-08-07.md).

## Deployed Service

| Item | Value |
|---|---|
| Panel UI | `https://games.alphasecunited.com/` through NPM; direct fallback `http://192.168.80.30/` |
| Wings API | `https://wings.alphasecunited.com/` through NPM; binds `0.0.0.0:8080` on the host |
| SFTP | `192.168.80.30:2022`, advertised by the panel as an alias so it bypasses NPM |
| Public Minecraft | `minecraft.alphasecunited.com`; DNS-only Cloudflare CNAME and Minecraft SRV records lead to Playit, which forwards only the game tunnel |
| Host | `game-01`, LXC 123 on `green-server`, `192.168.80.30/24` on SERVERS-A VLAN 80 |
| Versions | Pelican Panel v1.0.0-beta36, Wings v1.0.0-beta27, Docker 29.7.2, Playit agent 1.0.9 |
| Database | SQLite, in the `pelican-panel_pelican-data` Docker volume |
| Live panel configuration | `/opt/docker/pelican-panel/` on `game-01` |
| Server files | `/var/lib/pelican/volumes/<server-uuid>/`, owned `pelican` uid 999 gid 988 |

## Node Capacity

The panel enforces these against the 12 GiB LXC. They are what stops one server from taking the host down.

| Limit | Value |
|---|---|
| Memory | 10240 MiB allocatable, no overallocation |
| Disk | 51200 MiB allocatable, no overallocation |
| CPU | 600 percent, which is all six cores |
| Allocations | `192.168.80.30:25565` through `25575`, eleven ports |

## Servers

| Name | Egg | Release | State | Public | Allocation | Memory | CPU | Disk |
|---|---|---|---|---|---|---|---|---|
| Vanilla Minecraft 26.2 | Vanilla Minecraft | Minecraft Java Edition 26.2 | Running | Yes | `192.168.80.30:25565` | 8192 MiB | 400 percent | 20480 MiB |
| Better Realism MC 7.2.0 | Fabric | Better Realism server pack 7.2.0 | Stopped and retained | No | `192.168.80.30:25566` | 1024 MiB | 100 percent | 30720 MiB |

Vanilla uses the official Pelican egg, the Java 25 image, and the pinned installer value `VANILLA_VERSION=26.2`. Its Mojang server JAR matched the official SHA-1, it reached `Done (4.934s)!` on first boot, and it returned after a controlled restart in 0.257 seconds. The public status response is Minecraft 26.2, protocol 776, 0 of 20 players, with online authentication enabled.

The retained Better Realism server is Minecraft 1.21.1, Fabric Loader 0.19.3, Fabric Installer 1.1.2, and Java 21. Its UUID, 363 MiB volume, and world remain present. Its parked 1 GiB limit is below the 4 GiB initial heap in its startup command, so I must stop or shrink Vanilla and restore Better Realism's limits before trying to start it.

The old Best Vanilla World 2 server, world, container, and Pelican volume were deliberately deleted without a backup before this server was created. [Deployment.md](Documentation/Deployment.md) retains the historical troubleshooting record for that retired workload.

## Access

Trusted (10), Secure (50) and Secure Client (60) all reach the game ports, because `Allow Internal to AlphaSec-Servers` already permits every Internal network to this zone on every port. That policy predates this platform and I added nothing for game traffic. It also means Management, Server-Provision and Personal-A reach it, which is wider than the three networks I set out to allow.

Public players enter only `minecraft.alphasecunited.com`. The Minecraft client resolves the Cloudflare SRV record to the withheld Playit relay and its assigned port; Playit agent 1.0.9 runs natively on `game-01` and sends the connection to `127.0.0.1:25565`. A hardened `socat` unit relays that loopback socket to Pelican's allocation at `192.168.80.30:25565`.

The Pelican panel, Wings API, and SFTP service are not part of the Playit tunnel. I added no WAN port forward. The Cloudflare records are DNS-only, so Cloudflare does not proxy the Minecraft TCP stream.

## Known limits, not tracked as work

This platform runs the current Vanilla workload and retains Better Realism offline. Everything below is a property of the build I have accepted rather than work I owe.

- **No backups.** A lost world is lost. Pelican's own per-server backup feature writes into `/var/lib/pelican/backups` on the same host, so it survives a bad world edit but not the host. This is the standing no-backup rule, and it bites harder here than on a service whose state is rebuildable from `Configuration/`.
- **One active Minecraft server at a time.** Pelican assigns 9216 of 10240 MiB memory, 500 of 600 percent CPU, and all 51200 MiB of disk quota across the active Vanilla server and retained Better Realism record. Starting the retained pack requires a resource rebalance first.
- **NeoForge, Fabric, and Vanilla eggs are imported.** Paper and Valheim remain imports for the point when I need them.
- **Wings `check_permissions_on_boot` is on.** It walks both server volumes at start, so boot time grows as more worlds are added. Turn it off if that becomes material.
- **The image tracks `latest`.** Panel and Wings versions should move together, so a panel update without a matching Wings update can break the node. I record the deployed versions above instead of pinning, and check both after any pull.
