# Minecraft

**Created:** 2026-10-09  
**Last updated:** 2026-10-15

I run Vanilla Minecraft Java Edition 26.3 on `alpha-prod-01`, alongside TeamSpeak. Dockhand manages its Docker Compose stack. The server answers on the LAN and through the retained Playit tunnel. The public join name is `minecraft.alphasecunited.com`.

| Item | Value |
|---|---|
| Host | `alpha-prod-01`, VM 401 on `purple-server`, Debian 13, `192.168.80.118`, VLAN 80 |
| VM resources | Six vCPUs, 8 GiB RAM with the balloon minimum also at 8 GiB, 60 GiB NVMe-backed system disk |
| Server | Vanilla Java Edition 26.3, protocol 777, Temurin Java 25.0.4+7 |
| Container | `minecraft`, image `itzg/minecraft-server:stable-java25`, restart policy `unless-stopped`, DNS server pinned to `192.168.80.1` |
| Game endpoint | `192.168.80.118:25565/tcp`; also answers at `127.0.0.1:25565` on the host |
| Public endpoint | `minecraft.alphasecunited.com`, using a DNS-only CNAME and Minecraft SRV record in Cloudflare; the retained tunnel sends TCP traffic through the shared `playit-agent` to `127.0.0.1:25565`, with proxy protocol disabled |
| Java heap | 1 GiB initial, 4 GiB maximum |
| Container memory | 5 GiB; memory plus swap limit also 5 GiB, so the container cannot consume swap |
| Players | 20 maximum; online authentication enabled; RCON disabled |
| World and server files | `/opt/docker/minecraft/data/` on `alpha-prod-01`, mounted at `/data` |
| Editable Compose | `/opt/docker/dockhand/stacks/alpha_prod_01/minecraft/compose.yaml` on `docker-main`, in Dockhand environment 6 |
| Runtime Compose | `/opt/docker/hawser/stacks/minecraft/compose.yaml` on `alpha-prod-01` |
| Automatic updates | Excluded with `dockhand.update: "false"`; Minecraft itself is pinned to 26.3 |

The [Compose reference](Configuration/compose.yaml) matches Dockhand's saved definition. I verified the final container healthy, the Mojang server JAR checksum, LAN, loopback and public protocol responses, world persistence through container replacement, and the existing TeamSpeak paths on 2026-10-09. The [deployment record](Documentation/Change%20Records/Deployment%20-%202026-10-09.md) holds the VM changes and verification. The [status probe](Tests/README.md) checks Minecraft without joining as a player. Player login has not been tested.

The [DNS publication record](Documentation/Change%20Records/DNS%20Publication%20-%202026-10-09.md) verifies public DNS, the SRV status response and the login transport through the friendly name's resolved destination. Playit rejects the custom hostname when it is sent directly in the handshake, so the server-list ping can fail even though the SRV join route reaches the server. I have not completed an authenticated player join.

I applied the memory increase on 2026-10-11 and verified the live JVM limits, container health, retained world, Minecraft LAN/public responses and both TeamSpeak paths. The [change record](Documentation/Change%20Records/Memory%20and%20Operator%20Update%20-%202026-10-11.md) holds verification and the pending operator-name clarification. View distance and simulation distance remain 10. The [capacity check](Documentation/Capacity%20Research%20-%202026-10-11.md) records the earlier proposal; I have not load-tested player capacity.

I deleted the active world and started a fresh world on 2026-10-11, retaining Survival mode, Easy difficulty and an unset seed. The [world reset record](Documentation/Change%20Records/World%20Reset%20-%202026-10-11.md) confirms deletion, new world generation, empty player data, container health and LAN/public SRV responses. The retired `game-01` worlds were deleted on 2026-09-12; the [archived retirement record](../../Archive/Platforms/Game%20Servers/Documentation/Change%20Records/Game%2001%20Retirement%20-%202026-09-12.md) records that deletion and retention of the external Playit allocation. I keep no snapshots or backups.

I installed the [join welcome datapack](Source/alphasec_welcome/) on 2026-10-11. It sends the Mobi and Friends welcome, Discord name, and clickable Instagram, X, AlphaSec United and Duresa Kadi Portfolio links privately to joining players. The [change record](Documentation/Change%20Records/Join%20Welcome%20-%202026-10-11.md) records the live file hashes, enabled pack, function checks, save and healthy LAN/public responses. An authenticated join and reconnect remain untested. The pack lives in `world/datapacks/alphasec_welcome`; a future world reset must reinstall it.

On 2026-10-15, after the [Purple NIC outage that began on October 14](../../Security/Incidents/Galaxy/Purple%20Server%20NIC%20Transmit%20Hang%20-%202026-10-14.md), I found Minecraft had started before Alpha's resolver was populated. Server-list pings worked, but authentication service names failed to resolve; logins were most likely impaired from the 12:37 AM start at boot until 12:58:32 AM EDT. Nobody tried an authenticated join. I restarted the container at 12:58:13 AM with 0/20 players online, verified all three service names resolved and the container was healthy by 12:58:32 AM, and repeated the LAN ping at 12:59 AM. At 12:59:56 AM EDT I resolved `_minecraft._tcp.minecraft.alphasecunited.com` through 1.1.1.1 to `<playit-relay>`, connected and sent a protocol-777 handshake naming the SRV target with next state login, followed by Login Start as unauthenticated `testuser`. The first login packet was `0x01` Encryption Request, requiring online authentication, with a 245 ms round trip. I closed the connection before authentication. This verifies the Cloudflare SRV to Playit to server join route reaches authentication after the DNS correction; an authenticated join remains untested. The same race recurred after Purple's 9:06 AM reboot that morning, so I pinned the container's DNS server in its Compose definition at 9:19 AM ([change record](Documentation/Change%20Records/Pinned%20DNS%20Resolver%20-%202026-10-15.md)).

## Open items

- [x] Make external DNS survive a reboot. On 2026-10-15 I pinned `dns: [192.168.80.1]` in the Compose definition after the boot race hit twice that day. [Change record](Documentation/Change%20Records/Pinned%20DNS%20Resolver%20-%202026-10-15.md).
- [x] Confirm the pin across a reboot. A test reboot of `alpha-prod-01` at 9:24 AM on 2026-10-15 lost the race by 4.2 seconds, and the container still resolved all three authentication names without a restart ([reboot test](Documentation/Change%20Records/Pinned%20DNS%20Resolver%20-%202026-10-15.md#reboot-test)).
