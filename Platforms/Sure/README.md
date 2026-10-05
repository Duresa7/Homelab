# Sure

**Created:** 2026-10-05  
**Last updated:** 2026-10-05

I run Sure 0.7.5-hotfix.1, the community fork of Maybe Finance, at [sure.alphasecunited.com](https://sure.alphasecunited.com) on `docker-main`. It is my personal finance tracker. The first account comes from the standard application account and holds `super_admin`. Public sign-up is closed.

| Item | Value |
|---|---|
| Host | CT 110 `docker-main`, `grey-server`, `192.168.40.35`, VLAN 40 |
| Images | `ghcr.io/we-promise/sure:0.7.5-hotfix.1` for `web` and `worker`, `postgres:16`, `redis:8` |
| Containers | `sure-web`, `sure-worker` (Sidekiq), `sure-db`, `sure-redis`, all `unless-stopped` |
| Compose project | `/opt/docker/sure/docker-compose.yml`, project name `sure` |
| Persistent data | `/opt/docker/sure/data/storage` (uploads), `data/postgres`, `data/redis` |
| Secrets | `/opt/docker/sure/.env`, mode `0600`: `SECRET_KEY_BASE`, `POSTGRES_PASSWORD` and the three `ACTIVE_RECORD_ENCRYPTION_*` keys, all generated on the host |
| Backend | `http://192.168.40.35:3005`, health at `/up` |
| NPM | Proxy host 36, HTTP upstream `192.168.40.35:3005`, certificate 1, Force SSL, HTTP/2 and WebSockets enabled |
| DNS | UniFi local A record `6ac3e46b25574794b94ddd9b` to `192.168.85.2`, TTL 300; public lookup returns NXDOMAIN |
| Firewall | TCP 3005 added to `Allow NPM to docker-main web UIs` |
| Market data | Yahoo Finance for exchange rates and securities; returning HTTP 429 to my address on 2026-10-05 |
| Login | Standard application account email and password |
| MCP | `https://sure.alphasecunited.com/mcp`, OAuth; connected to [Executor](../Executor/README.md) as `sure` on 2026-10-05 |
| Logs | Docker `json-file`, 10 MiB per file, three files |

## Records and configuration

- [Explicit encryption keys](Documentation/Change%20Records/Explicit%20Encryption%20Keys%20-%202026-10-05.md)
- [Deployment and verification](Documentation/Change%20Records/Deployment%20-%202026-10-05.md)
- [Compose reference](Configuration/docker-compose.yml)
- [Environment template](Configuration/.env.example)

## Operating

I manage the stack from `/opt/docker/sure`. `docker compose config --quiet` validates the file, `docker compose ps` shows state, and `https://sure.alphasecunited.com/up` returns 200 when Rails is serving. `web` runs the database migrations on start, and the Sidekiq dashboard is at `/sidekiq` for the `super_admin`.

The three `ACTIVE_RECORD_ENCRYPTION_*` keys must never change. Sure encrypts user email, names, sessions and every provider token with them, so a new value makes all of that unreadable and breaks login. They are explicit values in `.env` and no longer depend on `SECRET_KEY_BASE`, but the `.env` file and `data/postgres` still belong together.

For upgrades I read the [release notes](https://github.com/we-promise/sure/releases), confirm the release's image tag exists on GHCR, change the pinned tag in both services, run `docker compose pull` and `docker compose up -d`, and then repeat the HTTPS and login checks. The official guide's update command is `docker compose up --no-deps -d web worker`.

Open items are listed at the end of the [deployment record](Documentation/Change%20Records/Deployment%20-%202026-10-05.md#open).
