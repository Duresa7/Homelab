# Game Servers

**Created:** 2026-08-07  
**Last updated:** 2026-08-09

I host my own game servers on `game-01`, an unprivileged LXC on `green-server`. Pelican Panel manages them through a web UI, and its Wings daemon runs each game server in its own Docker container with a memory, CPU and disk limit taken from the panel.

The current workload is Better Realism 7.2.0 on Minecraft 1.21.1 with Fabric. Adding a second Minecraft server, a different modpack, or a different game remains an egg import and a few clicks rather than a new platform deployment.

**Owner:** Platforms / Game Servers

## Layout

- [Configuration/](Configuration/) holds the panel Compose file, a redacted Wings configuration, and the loopback relay unit used by Playit.
- [Tests/](Tests/) holds the Minecraft status probe used for direct and SRV-based checks.
- [Documentation/Deployment.md](Documentation/Deployment.md) preserves the original platform build and first workload.
- [Better Realism MC and Playit Publication - 2026-08-09](Documentation/Change%20Records/Better%20Realism%20MC%20and%20Playit%20Publication%20-%202026-08-09.md) records the destructive workload replacement and public game path.

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

| Name | Egg | Pack release | Allocation | Memory | CPU | Disk |
|---|---|---|---|---|---|---|
| Better Realism MC 7.2.0 | Fabric | Better Realism server pack 7.2.0 | `192.168.80.30:25565` | 10240 MiB | 500 percent | 30720 MiB |

The August 3 CurseForge file is named `Better Realism (Server Pack) - MC 1.21.1 - 7.2.0`. Although the CurseForge view was filtered/tagged as game version 26.1.2, the archive's own `variables.txt` is authoritative: Minecraft **1.21.1**, Fabric Loader **0.19.3**, Fabric Installer **1.1.2**, and Java **21**. Wings reports 83 top-level mod jars and the runtime loads 163 mods. The startup command is `java -Xms4G -Xmx8G ... -jar server.jar`; the server reached `Done (11.261s)!` and idles at about 3.16 GiB of its 10.5 GiB container limit.

The old Best Vanilla World 2 server, world, container, and Pelican volume were deliberately deleted without a backup before this server was created. [Deployment.md](Documentation/Deployment.md) retains the historical troubleshooting record for that retired workload.

## Access

Trusted (10), Secure (50) and Secure Client (60) all reach the game ports, because `Allow Internal to AlphaSec-Servers` already permits every Internal network to this zone on every port. That policy predates this platform and I added nothing for game traffic. It also means Management, Server-Provision and Personal-A reach it, which is wider than the three networks I set out to allow.

Public players enter only `minecraft.alphasecunited.com`. The Minecraft client resolves the Cloudflare SRV record to the withheld Playit relay and its assigned port; Playit agent 1.0.9 runs natively on `game-01` and sends the connection to `127.0.0.1:25565`. A hardened `socat` unit relays that loopback socket to Pelican's allocation at `192.168.80.30:25565`.

The Pelican panel, Wings API, and SFTP service are not part of the Playit tunnel. I added no WAN port forward. The Cloudflare records are DNS-only, so Cloudflare does not proxy the Minecraft TCP stream.

## Known limits, not tracked as work

I closed this platform's backlog on 2026-08-08. It runs the workload I built it for, and everything below is a property of the build I have accepted rather than work I owe.

- **No backups.** A lost world is lost. Pelican's own per-server backup feature writes into `/var/lib/pelican/backups` on the same host, so it survives a bad world edit but not the host. This is the standing no-backup rule, and it bites harder here than on a service whose state is rebuildable from `Configuration/`.
- **One heavy pack at a time.** The 12 GiB guest gives this server a 10 GiB container limit. A second heavy pack needs a capacity review first.
- **Fabric and NeoForge eggs are imported.** Vanilla, Paper and Valheim remain one import call each in the panel, done at the moment I want one of them.
- **Wings `check_permissions_on_boot` is on.** It walks every server's files at start, so boot time grows as worlds are added. With one server it costs nothing. Turn it off if that changes.
- **The image tracks `latest`.** Panel and Wings versions should move together, so a panel update without a matching Wings update can break the node. I record the deployed versions above instead of pinning, and check both after any pull.
