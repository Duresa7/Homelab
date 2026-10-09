# Minecraft

**Created:** 2026-10-09  
**Last updated:** 2026-10-09

I run Vanilla Minecraft Java Edition 26.3 on `alpha-prod-01`, alongside TeamSpeak. Dockhand manages its Docker Compose stack. The server answers on the LAN; public Playit publication remains open.

| Item | Value |
|---|---|
| Host | `alpha-prod-01`, VM 401 on `purple-server`, Debian 13, `192.168.80.118`, VLAN 80 |
| VM resources | Six vCPUs, 6 GiB RAM with the balloon minimum also at 6 GiB, 60 GiB NVMe-backed system disk |
| Server | Vanilla Java Edition 26.3, protocol 777, Temurin Java 25.0.4+7 |
| Container | `minecraft`, image `itzg/minecraft-server:stable-java25`, restart policy `unless-stopped` |
| Game endpoint | `192.168.80.118:25565/tcp`; also answers at `127.0.0.1:25565` on the host |
| Java heap | 1 GiB initial, 2 GiB maximum |
| Container memory | 3 GiB; memory plus swap limit also 3 GiB, so the container cannot consume swap |
| Players | 20 maximum; online authentication enabled; RCON disabled |
| World and server files | `/opt/docker/minecraft/data/` on `alpha-prod-01`, mounted at `/data` |
| Editable Compose | `/opt/docker/dockhand/stacks/alpha_prod_01/minecraft/compose.yaml` on `docker-main`, in Dockhand environment 6 |
| Runtime Compose | `/opt/docker/hawser/stacks/minecraft/compose.yaml` on `alpha-prod-01` |
| Automatic updates | Excluded with `dockhand.update: "false"`; Minecraft itself is pinned to 26.3 |

The [Compose reference](Configuration/compose.yaml) matches Dockhand's saved definition. I verified the final container healthy, the Mojang server JAR checksum, LAN and loopback protocol responses, world persistence through container replacement, and the existing TeamSpeak paths on 2026-10-09. The [deployment record](Documentation/Change%20Records/Deployment%20-%202026-10-09.md) holds the VM changes, verification and open publication work. The [status probe](Tests/README.md) checks Minecraft without joining as a player.

I created a new world. The retired `game-01` worlds were deleted on 2026-09-12; the [archived retirement record](../../Archive/Platforms/Game%20Servers/Documentation/Change%20Records/Game%2001%20Retirement%20-%202026-09-12.md) records that deletion and retention of the external Playit allocation. I keep no snapshots or backups.
