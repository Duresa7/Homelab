# Better Realism MC and Playit Publication

**Created:** 2026-08-09  
**Last updated:** 2026-08-09

**Implemented:** 2026-08-09  
**Owner:** Platforms / Game Servers  
**Host:** `game-01`, LXC 123 on `green-server`, `192.168.80.30`  
**Status:** Complete. Better Realism 7.2.0 is running under Fabric, and `minecraft.alphasecunited.com` reaches it through Cloudflare DNS and Playit without publishing the Pelican interfaces.

## Outcome

I permanently deleted the existing Best Vanilla World 2 Pelican server and its world without a backup, as requested, then created a clean Fabric server for Better Realism 7.2.0. I reused the existing `192.168.80.30:25565` allocation and retained the panel's 10240 MiB memory, 500 percent CPU, and 30720 MiB disk limits.

Players enter only:

```text
minecraft.alphasecunited.com
```

The public path is:

```text
Minecraft client
  -> Cloudflare DNS-only CNAME and Minecraft SRV records
  -> <REDACTED_MINECRAFT_RELAY_HOST>:26328
  -> Playit agent 1.0.9 on game-01
  -> 127.0.0.1:25565
  -> minecraft-playit-relay.service
  -> 192.168.80.30:25565
  -> Pelican-managed Minecraft container
```

The relay hostname is withheld from this public repository. The friendly domain and port are not credentials.

## Release selection

The requested CurseForge file is [file 8570131](https://www.curseforge.com/minecraft/modpacks/better-realism-mc/files/8570131), published on 2026-08-03 as `Better Realism (Server Pack) - MC 1.21.1 - 7.2.0`.

The CurseForge view was filtered/tagged as game version 26.1.2, but the server archive's own `variables.txt` declares the runtime that actually installs:

| Item | Value |
| --- | --- |
| Minecraft | 1.21.1 |
| Loader | Fabric 0.19.3 |
| Fabric installer | 1.1.2 |
| Java | 21 |
| Archive size | 220,866,142 bytes |
| Archive SHA-256 | `c1fcb51031edb8aa1f30cb0cd7efac18d3e214ac780378d5c9a69222b4a6d733` |

I used those internal values instead of forcing the CurseForge filter label onto the server. The extracted pack supplied 83 top-level mod jars and 229 configuration files; Fabric reports 163 runtime mods after including libraries.

## Destructive replacement

I stopped and deleted the old server through Pelican's server deletion service. I then verified all three effects before creating the replacement:

- the Pelican server count dropped to zero;
- the allocation was released;
- the old Docker container and old server volume no longer existed.

There was no backup or snapshot. The old world is not recoverable from this platform.

I imported Pelican's official Fabric egg from the upstream eggs repository at commit `75bf05db3c6c305e0fa6eef1d38c7e7176121de9`, then created `Better Realism MC 7.2.0` with:

| Setting | Value |
| --- | --- |
| Image | `ghcr.io/pelican-eggs/yolks:java_21` |
| Startup | `java -Xms4G -Xmx8G -Dterminal.jline=false -Dterminal.ansi=true -jar server.jar` |
| Memory / swap | 10240 MiB / 0 MiB |
| CPU | 500 percent |
| Disk | 30720 MiB |
| Allocation | `192.168.80.30:25565` |

I extracted only `mods/` and `config/`, accepted the Mojang EULA, restored Pelican ownership, and started the server through the panel. The downloaded archive was removed after the deployed files and runtime were verified.

## Playit and Cloudflare

I installed Playit agent 1.0.9 from its Debian package repository directly on `game-01`, claimed it to the existing account, assigned the existing Minecraft tunnel to this agent, and restarted the service after the assignment. Its persistent secret remains only at `/etc/playit/playit.toml`, owned `playit:playit` at mode 0600.

The Playit origin remains exactly the requested configuration:

| Setting | Value |
| --- | --- |
| Local IP | `127.0.0.1` |
| Local port | 25565 |
| Proxy Protocol | None |

Pelican publishes the game container on the host's VLAN address rather than loopback, so [minecraft-playit-relay.service](../../Configuration/minecraft-playit-relay.service) bridges the two sockets. It uses a dynamic systemd user, starts at boot, and has no Playit credential or tunnel identity in the unit.

I added these records to the `alphasecunited.com` Cloudflare zone:

| Type | Name | Value | TTL | Proxy |
| --- | --- | --- | --- | --- |
| CNAME | `minecraft.alphasecunited.com` | `<REDACTED_MINECRAFT_RELAY_HOST>` | 300 | DNS-only |
| SRV | `_minecraft._tcp.minecraft.alphasecunited.com` | priority 1, weight 1, port 26328, target `<REDACTED_MINECRAFT_RELAY_HOST>` | 300 | n/a |

Playit's own native custom-domain feature offered a $30/year Premium add-on. I did not purchase it. Minecraft's standard SRV discovery provides the requested one-name connection without that subscription.

The Playit tunnel carries only Minecraft. `games.alphasecunited.com`, `wings.alphasecunited.com`, SFTP, and the Pelican administrative interfaces were not added to Playit, and I created no WAN port forward.

## Verification

| Check | Result |
| --- | --- |
| Fabric boot | `Loading Minecraft 1.21.1 with Fabric Loader 0.19.3`; 163 mods; `Done (11.261s)!` |
| Local status through loopback relay | Minecraft 1.21.1, protocol 767, 0 of 20 players |
| DNS CNAME | resolves to `<REDACTED_MINECRAFT_RELAY_HOST>` |
| DNS SRV | priority 1, weight 1, port 26328, withheld relay target |
| Public SRV status | `minecraft.alphasecunited.com` returned Minecraft 1.21.1, protocol 767, 0 of 20 players in 114.5 ms |
| Playit | agent claimed; `playit.service` enabled and active with live control connections |
| Relay | `minecraft-playit-relay.service` enabled and active; loopback listener and backend connection both passed |
| Pelican interfaces | panel returned HTTP 302 and Wings returned HTTP 401 on their internal host paths |
| Host health | healthy; 28.98 percent memory used, root disk 8 percent used |
| Minecraft container | running; 3.163 GiB of its 10.5 GiB limit at final check |

A low-level test that forced the friendly hostname directly onto port 26328 reset at the relay because it skipped Minecraft SRV discovery. [minecraft-status.py](../../Tests/minecraft-status.py) now has `--srv` mode so the repository test follows the same path as a Minecraft client and does not disclose the relay hostname.

The server log contains non-fatal warnings for optional mixin targets, missing data fixers in some mods, empty Moonlight registries, and one `adorable_eggs` loot-table key. None prevented the server from reaching `Done`, answering status, or remaining up.

## Cleanup and remaining validation

I removed the one-time Playit claim URL, temporary authenticated browser profiles, the remote claim transcript, the downloaded server archive, and the temporary cross-host relay used while locating the correct Playit agent. The existing TeamSpeak Playit container on `alpha-prod-01` stayed running throughout.

The automated acceptance check proves DNS discovery, the public Playit path, the Fabric runtime, and the Minecraft status protocol. A real Better Realism 7.2.0 client login remains a player-side compatibility check; I did not fabricate one without the modded client.
