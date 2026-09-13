# Game Servers Configuration

**Created:** 2026-08-07  
**Last updated:** 2026-08-09

Versioned reference copies of the files `game-01` actually reads. None is a backup, and none is restored from here without checking it against the live host first.

| File | Live path on `game-01` | Owner |
|---|---|---|
| [docker-compose.yml](docker-compose.yml) | `/opt/docker/pelican-panel/compose.yml` | I edit this, then `docker compose up -d` |
| [wings-config.yml](wings-config.yml) | `/etc/pelican/config.yml`, mode 0600 | The panel generates it |
| [minecraft-playit-relay.service](minecraft-playit-relay.service) | `/etc/systemd/system/minecraft-playit-relay.service` | I edit this; systemd runs it with a dynamic user |

`wings-config.yml` carries three withheld values: `uuid`, `token_id`, and `token`. They are the node's credentials to the panel. Everything else in the file is published as-is.

I do not hand-edit `/etc/pelican/config.yml` on the host. Re-downloading the node configuration from the panel overwrites the whole file, so a hand edit survives only until the next fetch. Node settings change in the panel, and the file follows.

Per-server settings do not live here. Pelican keeps them in its own SQLite database inside the `pelican-panel_pelican-data` Docker volume, and the server files themselves sit under `/var/lib/pelican/volumes/<server-uuid>/`. Rebuilding this host means reinstalling the panel from `docker-compose.yml` and recreating the servers, not restoring a file from this folder.

The Playit agent secret is not versioned. The package keeps it at `/etc/playit/playit.toml`, owned by `playit:playit` at mode 0600. The relay unit contains no Playit identity: it listens only on `127.0.0.1:25565` and forwards to the Pelican allocation on the same host.
