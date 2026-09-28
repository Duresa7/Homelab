# BookOrbit

**Created:** 2026-09-28  
**Last updated:** 2026-09-28

I run BookOrbit v3.1.0 on `docker-main` at [booklore.alphasecunited.com](https://booklore.alphasecunited.com). It replaced BookLore on 2026-09-28, keeping the existing HTTPS address and NPM upstream.

| Item | Verified 2026-09-28 |
|---|---|
| Project | `/opt/docker/bookorbit` |
| Application | `bookorbit-app`, v3.1.0, host TCP 6060 to container TCP 3000 |
| Database | `bookorbit-db`, PostgreSQL 18.6 with pgvector, internal TCP 5432 |
| Library | 42 books from `/data/booklore/books`, mounted read/write at `/books` |
| Application data | `/opt/docker/bookorbit/data/app`, owned by UID/GID 1000 |
| Database data | `/opt/docker/bookorbit/data/postgres` |

I verified a fresh login with my standard application account, authenticated file requests for all 42 books through HTTPS, and HTTP 200 from the application. The [migration record](Documentation/Change%20Records/Migration%20from%20BookLore%20-%202026-09-28.md) records the imported data and completed cutover.

The [Compose reference](Configuration/docker-compose.yml) matches the active deployment. Its `.env` stays on the host with mode 0600. `APP_IMAGE` is pinned to `ghcr.io/bookorbit/bookorbit@sha256:78b6eac18306eb7eba0dbf6592ecdee01b15f24de9a941cb853db4a0232d7999`, the digest of the running v3.1.0 image. The optional TTS profile is not enabled. Library watching, file metadata writes, and file renaming are disabled.

The direct fallback is `http://192.168.40.35:6060`. NPM host 10 still uses that backend. Dockhand manages the new project, and the Homarr shortcut now says BookOrbit. I removed the old BookLore and MariaDB containers and their Docker network.

I retained the original database at `/data/booklore/mariadb/config` and application data at `/data/booklore/data` for settings the importer does not support. The original Compose project moved to `/opt/retired/booklore`; it is no longer an active Dockhand stack. The books remain at their original path as BookOrbit's active library. I created no backup or snapshot.
