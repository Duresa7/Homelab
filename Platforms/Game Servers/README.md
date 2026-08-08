# Game Servers

**Created:** 2026-08-07  
**Last updated:** 2026-08-08

I host my own game servers on `game-01`, an unprivileged LXC on `green-server`. Pelican Panel manages them through a web UI, and its Wings daemon runs each game server in its own Docker container with a memory, CPU and disk limit taken from the panel.

The first workload is a 231-mod NeoForge modpack. Adding a second Minecraft server, a different modpack, or a different game is an egg import and a few clicks rather than a new deployment.

**Owner:** Platforms / Game Servers

## Layout

- [Configuration/](Configuration/) holds the two files the host reads: the panel's Compose file and a redacted copy of the Wings node configuration.
- [Documentation/Deployment.md](Documentation/Deployment.md) is the build record, including the parts that did not work the first time.

The guest itself belongs to Galaxy, not here. Its creation record is [Galaxy Game-01 LXC Deployment - 2026-08-07](../../Infrastructure/Compute/Galaxy/Documentation/Change%20Records/Galaxy%20Game-01%20LXC%20Deployment%20-%202026-08-07.md).

## Deployed Service

| Item | Value |
|---|---|
| Panel UI | `https://games.alphasecunited.com/` through NPM; direct fallback `http://192.168.80.30/` |
| Wings API | `https://wings.alphasecunited.com/` through NPM; binds `0.0.0.0:8080` on the host |
| SFTP | `192.168.80.30:2022`, advertised by the panel as an alias so it bypasses NPM |
| Host | `game-01`, LXC 123 on `green-server`, `192.168.80.30/24` on SERVERS-A VLAN 80 |
| Versions | Pelican Panel v1.0.0-beta36, Wings v1.0.0-beta27, Docker 29.7.2 |
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
| Best Vanilla World 2 | NeoForge | Serverpack MC 26.1.2-2.1.0 | `192.168.80.30:25565` | 10240 MiB | 500 percent | 30720 MiB |

Minecraft **26.1.2** on NeoForge **26.1.2.78**, Java 25, 103 active mods of 122 shipped, from `Best Vanilla World 2 Serverpack MC 26.1.2-2.1.0`. The startup command sets `-Xms8G -Xmx8G` rather than the egg's default `-XX:MaxRAMPercentage=95.0`, which would leave almost nothing of the container limit for metaspace, GC structures and direct buffers. The server reached `Done (1.375s)` and settled at 5.74 GiB of its 10.5 GiB limit with no player connected.

**The serverpack has to match the release the players installed, not merely the Minecraft version.** I first deployed the `26.2-1.0.0` serverpack, whose metadata is wrong three ways: it is tagged game version 26.2 while every mod inside is built for `mc26.1.2`, its `variables.txt` declares `MODLOADER_VERSION=21.2.1-beta` for Minecraft 1.21.2, and ServerPackCreator left Sodium enabled. I derived NeoForge `26.1.2.94` from the mod filenames to get it running, and it ran fine. It also refused every player, because the client release they had installed pins NeoForge `26.1.2.78`, and a loader mismatch fails the handshake. Moving to the matching `26.1.2-2.1.0` serverpack fixed it, and that pack states its own loader version honestly. [Deployment.md](Documentation/Deployment.md) has the full trail.

I keep the 19 `.disabled` client mods in place rather than deleting them, so a later pack update can be diffed against what the author shipped.

## Access

Trusted (10), Secure (50) and Secure Client (60) all reach the game ports, because `Allow Internal to AlphaSec-Servers` already permits every Internal network to this zone on every port. That policy predates this platform and I added nothing for game traffic. It also means Management, Server-Provision and Personal-A reach it, which is wider than the three networks I set out to allow.

Nothing is published to the internet. There are no WAN port forwards and no tunnel. The `Game-Access` WireGuard server on `10.66.200.1/24` port 51823 exists and is enabled, but no policy points it at this host yet.

## Known limits, not tracked as work

I closed this platform's backlog on 2026-08-08. It runs the workload I built it for, and everything below is a property of the build I have accepted rather than work I owe.

- **No backups.** A lost world is lost. Pelican's own per-server backup feature writes into `/var/lib/pelican/backups` on the same host, so it survives a bad world edit but not the host. This is the standing no-backup rule, and it bites harder here than on a service whose state is rebuildable from `Configuration/`.
- **One heavy pack at a time.** Green has 8.2 GiB free with this server idle. A second 231-mod pack needs roughly the same again, which means replacing green's two 8 GB DIMMs.
- **Only the NeoForge egg is imported.** Vanilla, Paper and Valheim are one import call each in the panel, done at the moment I want one of them. There is nothing to prepare in advance.
- **Wings `check_permissions_on_boot` is on.** It walks every server's files at start, so boot time grows as worlds are added. With one server it costs nothing. Turn it off if that changes.
- **The image tracks `latest`.** Panel and Wings versions should move together, so a panel update without a matching Wings update can break the node. I record the deployed versions above instead of pinning, and check both after any pull.
