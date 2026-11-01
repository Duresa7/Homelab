# Flight kick disabled

**Created:** 2026-11-01  
**Last updated:** 2026-11-01

On 2026-11-01 I set `allow-flight=true` on the Minecraft server. Players are no longer kicked with "Flying is not enabled on this server" when the server sees them in the air for too long. The setting does not give survival players flight. It only removes the kick.

## Why

At 3:35:14 AM the server kicked one of two players with `was kicked for floating too long!`. At 3:35:54 AM the Playit agent logged `timeout reading claim token response` on that player's first reconnect. At 3:36:37 AM the second player dropped with `Timed out`. Both rejoined by 3:37:38 AM. The server logged no `Can't keep up` warnings that night, the container had not restarted, and Purple's kernel log since midnight had no NIC hang or link change. I read the kick as connection lag through the tunnel: the server stopped getting movement updates while the player was off the ground and treated it as flying.

The trade-off is that a modified client could fly without being kicked. Online authentication stays on, and the server has no other anti-cheat.

## What changed

One line in the `minecraft` service's environment:

```yaml
      MAX_PLAYERS: "20"
      ALLOW_FLIGHT: "TRUE"
```

The image writes `server.properties` from these variables at each start, so a hand edit of `server.properties` would not last.

Before the change, all three copies of the definition were identical at SHA-256 `84f0b50aa8eca298853cafb057600669d738f951edb6a9d9a037af939cf46b63`. I wrote the same bytes to all three, SHA-256 `2ca07ac58539215b7406db8c5e93e95c630700e1b485ab4b0b1e87ff2adb7154`:

- Dockhand's saved definition on `docker-main`, `/opt/docker/dockhand/stacks/alpha_prod_01/minecraft/compose.yaml`.
- The runtime file on `alpha-prod-01`, `/opt/docker/hawser/stacks/minecraft/compose.yaml`.
- The repository [Compose reference](../../Configuration/compose.yaml).

I made no host copy of the old file, because the repository reference held the same bytes and git keeps its history. `docker compose config -q` passed on Alpha.

The LAN status probe showed 0 of 20 players at 6:01:25 AM. At 6:01:31 AM I ran `docker compose -p minecraft up -d --no-build --pull never` in the runtime directory on Alpha, which recreated the container from the existing image under the same project Dockhand uses.

## Verification

- The container was healthy at 6:01:52 AM, with restart count 0, start time 6:01:34 AM and `HostConfig.Dns` still `[192.168.80.1]`.
- The container environment holds `ALLOW_FLIGHT=TRUE`, and `/data/server.properties` reads `allow-flight=true`. `max-players=20`, `online-mode=true`, `view-distance=10` and the MOTD are unchanged.
- At 6:01:45 AM the log shows `Preparing level "world"` and `Done (0.275s)`, loading the existing world.
- `sessionserver.mojang.com` resolves inside the container, and the `alphasec_welcome` datapack is still in `world/datapacks`.
- At 6:01:55 AM the status probe returned 26.3 / 777 / 0 of 20 on the LAN in 6.1 ms and through the Cloudflare SRV record and Playit in 223.2 ms.

Minecraft was unavailable for about 15 seconds.

## Old backup copies removed

The [pinned DNS change](Pinned%20DNS%20Resolver%20-%202026-10-15.md) left `/root/minecraft-compose.pre-dns-2026-10-15.yaml` on both `alpha-prod-01` and `docker-main`. Both copies hashed to `34b6f49e959e45a80bec5775ffb30e62b4014ea0ab2a5165bda2f7208a9855c3`, the same bytes as the Compose reference in commit `c1b71550`, so they held no withheld values. I committed that file as [`alpha-prod-01-minecraft-compose-2026-10-15.yaml`](../../../../Backups/alpha-prod-01-minecraft-compose-2026-10-15.yaml) and deleted both host copies. Neither host's `/root` holds a Minecraft file now.

## Rollback

Delete the `ALLOW_FLIGHT` line from both live files, run `docker compose -p minecraft up -d` in `/opt/docker/hawser/stacks/minecraft` on Alpha, and revert the repository reference.
