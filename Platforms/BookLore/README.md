# BookLore

**Created:** 2026-09-13  
**Last updated:** 2026-09-27

I run BookLore, my e-book library, on `docker-main` from `/opt/docker/booklore`.

| Item | Value (read 2026-09-24) |
|---|---|
| BookLore | v2.4.0, container `booklore`, TCP 6060 |
| Database | MariaDB 11.4.8, container `mariadb` |
| Internal URL | `https://booklore.alphasecunited.com`, NPM proxy host 10 |
| Direct fallback | `http://192.168.40.35:6060` |

Its MariaDB dependency stays on `lscr.io/linuxserver/mariadb:11.4.8`, the application-supported pin recorded in the [dependency update](../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-03.md).

The [Compose override](Configuration/docker-compose.override.yml) is deployed beside the existing `docker-compose.yml`. Its WUD labels were added to restrict database update suggestions to the 11.4.8 tag. I retired WUD on 2026-09-27; those labels are now inert and I left the running database unchanged. A future dependency change must still review the image pin. The main Compose file and database credentials remain on the host; this override is not a complete deployment definition.

The [2026-09-13 maintenance record](../../Operations/Maintenance/Container%20Image%20Updates%20-%202026-09-13.md) contains the recreation and health checks.
