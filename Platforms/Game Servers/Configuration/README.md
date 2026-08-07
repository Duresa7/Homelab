# Game Servers Configuration

**Created:** 2026-08-07  
**Last updated:** 2026-08-07

Versioned reference copies of the two files `game-01` actually reads. Neither is a backup, and neither is restored from here without checking it against the live host first.

| File | Live path on `game-01` | Owner |
|---|---|---|
| [docker-compose.yml](docker-compose.yml) | `/opt/docker/pelican-panel/compose.yml` | I edit this, then `docker compose up -d` |
| [wings-config.yml](wings-config.yml) | `/etc/pelican/config.yml`, mode 0600 | The panel generates it |

`wings-config.yml` carries three withheld values: `uuid`, `token_id`, and `token`. They are the node's credentials to the panel. Everything else in the file is published as-is.

I do not hand-edit `/etc/pelican/config.yml` on the host. Re-downloading the node configuration from the panel overwrites the whole file, so a hand edit survives only until the next fetch. Node settings change in the panel, and the file follows.

Per-server settings do not live here. Pelican keeps them in its own SQLite database inside the `pelican-panel_pelican-data` Docker volume, and the server files themselves sit under `/var/lib/pelican/volumes/<server-uuid>/`. Rebuilding this host means reinstalling the panel from `docker-compose.yml` and recreating the servers, not restoring a file from this folder.
